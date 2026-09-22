"""Bounded, read-only projections of published evidence; no scientific reclassification."""
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query
from .db import query, one

router = APIRouter(prefix="/api", tags=["evidence"])


from .evidence_common import require_protein, cursor_read, cursor_write, fields, clean
from .variant_support import variant_conditions, FREQUENCIES, FREQUENCY_LABELS, TRANSCRIPT_LABELS,transcript_status as classify_transcript, amino_change, canonical_rows, page_source_evidence, raw_predictions_for_rows


def prediction_group(field):
    if field.startswith("alphagenome_"):
        return "AlphaGenome"
    if field.startswith("Aloft_"):
        return "Loss of function"
    if field.startswith(("phyloP", "phastCons", "GERP", "bStatistic")):
        return "Conservation and background"
    if field.startswith(("ESM1b", "AlphaMissense", "popEVE", "GPN_MSA", "PrimateAI", "MutFormer")):
        return "Sequence models"
    if field.startswith(("SIFT", "PROVEAN", "Polyphen", "MutationTaster", "MutationAssessor", "MutPred")):
        return "Amino acid substitution"
    return "Integrated effect predictions"


@lru_cache(maxsize=1)
def prediction_dictionary():
    result = query("SELECT field,source,scope,tool FROM web_variant.variant_prediction_field ORDER BY field")
    for field, label in [("alphagenome_avi_raw", "AVI raw"), ("alphagenome_avi_phred", "AVI PHRED"), ("alphagenome_splicing", "Merged splicing")]:
        if not any(r["field"] == field for r in result):
            result.append({"field": field, "source": "AlphaGenome", "scope": "variant", "tool": "AlphaGenome", "label":label})
    return result


def predictions(variant, consequence, selected=None):
    result = []
    for definition in prediction_dictionary():
        key = definition["field"]
        if selected is not None and key not in selected:
            continue
        data = consequence if definition["scope"] == "transcript_consequence" else variant
        status = data.get(key + "_status")
        if key.startswith("alphagenome_"):
            status = variant.get("splicing_status" if key.endswith("splicing") else "avi_status")
        result.append({**definition, "value": clean(data.get(key)), "status": status,
                       "group": prediction_group(key)})
    return result


@lru_cache(maxsize=256)
def variant_filters(accession):
    consequences = query('''SELECT DISTINCT unnest(string_to_array(c."Consequence", '&')) AS value
        FROM web_variant.variant_consequence c JOIN web.protein_gene g ON g.hgnc_id=c.gene_id
        WHERE g.accession=:accession ORDER BY value''', {"accession": accession})
    # Available primary source categories are defined by the published source dictionary.
    sources = query("SELECT source FROM web_variant.variant_dataset WHERE source IN ('ClinVar','COSMIC','gnomAD') ORDER BY source")
    return {"sources": [r["source"] for r in sources]+["dbSNP"], "consequences": [r["value"] for r in consequences],
            "predictors": [{**p,"group":prediction_group(p["field"])} for p in prediction_dictionary()],
            "transcript_statuses":[{"value":"all","label":"All selected transcripts"}]+[{"value":k,"label":v} for k,v in TRANSCRIPT_LABELS.items()],
            "frequency_types": [{"value":k,"label":FREQUENCY_LABELS[k]} for k in FREQUENCIES]}


@router.get("/proteins/{accession}/variants")
def variants(accession: str, source: str = "", consequence: str = "", position: int | None = None,
             limit: int = Query(20, ge=1, le=100), cursor: str = "", search: str = Query('',max_length=200),
             canonical_start: int | None = None, canonical_end: int | None = None, frequency: str = 'overall',
             clinvar: str = '', af_min: float | None = None, af_max: float | None = None, af_status: str = '',
             predictors: str = 'CADD_phred,REVEL_score,SIFT_score',transcript_status:str='all',
             offset: int = Query(0, ge=0)):
    where,params,protein = variant_conditions(accession,source,consequence,position,search,canonical_start,canonical_end,frequency,clinvar,af_min,af_max,af_status,transcript_status)
    selected=list(dict.fromkeys(p.strip() for p in predictors.split(',') if p.strip())) if predictors!='none' else []
    definitions={p['field']:p for p in prediction_dictionary()}
    if any(p not in definitions for p in selected):
        raise HTTPException(422,'Choose known predictors from the published dictionary')
    context = ["variants", accession, source, consequence, position,search,canonical_start,canonical_end,frequency,clinvar,af_min,af_max,af_status,predictors,transcript_status]
    after = cursor_read(cursor, context)
    params['limit']=limit+1
    params['offset']=0 if cursor else offset
    if after:
        where+=" AND (c.variant_id,c.annotation_id,c.gene_id) > (:vid,:aid,:gid)"
        params.update(vid=after[0],aid=after[1],gid=after[2])
    score_columns=[]
    for field in selected:
        alias='c' if definitions[field]['scope']=='transcript_consequence' else 'v'
        status='splicing_status' if field=='alphagenome_splicing' else 'avi_status' if field.startswith('alphagenome_') else field+'_status'
        score_columns.extend([alias+'."'+field+'"',alias+'."'+status+'"'])
    extra=', '+','.join(dict.fromkeys(score_columns)) if score_columns else ''
    rows=query('''WITH page AS MATERIALIZED (SELECT c.* FROM web_variant.variant_consequence c WHERE '''+where+'''
        ORDER BY c.variant_id,c.annotation_id,c.gene_id LIMIT :limit OFFSET :offset)
        SELECT c.variant_id,c.annotation_id,c.gene_id,v.chrom chromosome,v.pos position,v.ref,v.alt,
        c."HGVSp" hgvsp,c."HGVSc" hgvsc,c."Consequence" consequence,c."Feature" transcript_id,
        c.selection_method,c."CANONICAL" canonical_raw,c."Feature_type" feature_type,c.matches_json,f."'''+FREQUENCIES[frequency]+'''" af,f.frequency_status'''+extra+'''
        FROM page c JOIN web_variant.variant v USING(variant_id)
        LEFT JOIN web_variant.variant_frequency f USING(variant_id)
        ORDER BY c.variant_id,c.annotation_id,c.gene_id''',params)
    page=rows[:limit];ids=list({r['variant_id'] for r in page})
    source_map={}
    if ids:
        for row in query('SELECT variant_id,database_name FROM web_variant.variant_database WHERE variant_id=ANY(:ids)',{'ids':ids}):
            source_map.setdefault(row['variant_id'],set()).add(row['database_name'])
    source_evidence=page_source_evidence(ids)
    canonical=canonical_rows(ids,protein['sequence_id'])
    for row in page:
        row.update(amino_change(row['hgvsp']))
        row.update(transcript_status=classify_transcript(row['feature_type'],row['transcript_id'],row['canonical_raw']),assembly='GRCh38')
        row['source_names']=sorted(source_map.get(row['variant_id'],[]))
        value=row.pop('af');record_status=row.pop('frequency_status')
        row['frequency']={'af':value,'population':frequency,'label':FREQUENCY_LABELS[frequency],
                          'status':record_status if value is not None else ('no_value_for_population' if record_status else 'no_local_frequency_record'),
                          'record_status':record_status,'source':'gnomAD exomes 4.1'}
        row['predictions']=predictions(row,row,set(selected))
        row['predictions'].sort(key=lambda p:selected.index(p['field']))
        row['clinvar']=[{'classification':r['classification'],'review_status':r['review_status'],'origin':r['origin'],
                         'oncogenicity':r['oncogenicity'],'somatic_clinical_impact':r['somatic_clinical_impact'],'source_id':r['native_id']}
                        for r in source_evidence if r['variant_id']==row['variant_id'] and r['source']=='ClinVar']
        row['cosmic']={'present':'COSMIC' in row['source_names'],'source_ids':list(dict.fromkeys(r['native_id'] for r in source_evidence if r['variant_id']==row['variant_id'] and r['source']=='COSMIC'))}
        row['canonical_positions']=[{k:r[k] for k in ('sequence_id','position','ref_aa','alt_aa')} for r in canonical
                                    if r['variant_id']==row['variant_id'] and r['annotation_id']==row['annotation_id'] and r['gene_id']==row['gene_id']]
    raw_predictions_for_rows(page,selected)
    for row in page:
        row.pop('matches_json',None)
        for field in selected:
            row.pop(field,None);row.pop(field+'_status',None)
        row.pop('avi_status',None);row.pop('splicing_status',None)
    next_cursor=cursor_write([page[-1][k] for k in ('variant_id','annotation_id','gene_id')],context) if len(rows)>limit else None
    return {'items':page,'next_cursor':next_cursor,'filters':variant_filters(accession),'coordinate_system':'GRCh38',
            'sequence_mapping_note':'Single-letter AA labels refer to the selected transcript; only canonical_positions has a verified current UniProt sequence relation.'}


@router.get("/variants/{variant_id}")
def variant_detail(variant_id: str, accession: str = ""):
    variant = one("SELECT * FROM web_variant.variant WHERE variant_id=:id", {"id": variant_id})
    if not variant:
        raise HTTPException(404, "Variant not found")
    params = {"id": variant_id, "accession": accession}
    condition = " AND EXISTS (SELECT 1 FROM web.protein_gene g WHERE g.hgnc_id=c.gene_id AND g.accession=:accession)" if accession else ""
    consequences = query("SELECT c.* FROM web_variant.variant_consequence c WHERE c.variant_id=:id" + condition + " ORDER BY c.annotation_id,c.gene_id", params)
    if accession and not consequences:
        raise HTTPException(404, "Variant is not associated with this protein's gene")
    genes = sorted({c['gene_id'] for c in consequences})
    sequence_status = {r['gene_id']: r for r in query('''SELECT gene_id,transcript_id,transcript_stable_id,protein_id,protein_stable_id,
        selection_method,input_sequence_status,input_sequence_source,input_sequence_length,
        comparison_status,status_reason,comparison_method,exact_match_sequence_count
        FROM web_variant_sequence.representative_protein_sequence_status WHERE gene_id = ANY(:genes)''', {'genes': genes})}
    exact_targets = {}
    for r in query('''SELECT gene_id,target_accession,target_sequence_id,target_sequence_kind,target_isoform_id,
        match_evidence,coordinate_relation_status FROM web_variant_sequence.representative_uniprot_sequence_relation
        WHERE gene_id = ANY(:genes) AND is_exact_match = true ORDER BY gene_id,target_accession,target_sequence_id''', {'genes': genes}):
        exact_targets.setdefault(r.pop('gene_id'), []).append(r)
    groups = {}
    score_rows=[{**c,'predictions':predictions(variant,c)} for c in consequences]
    raw_predictions_for_rows(score_rows,[p['field'] for p in prediction_dictionary()])
    for c,score_row in zip(consequences,score_rows):
        for p in score_row['predictions']:
            # Variant scores appear once; transcript scores retain their exact annotation identity.
            if p["scope"] != "transcript_consequence" and c is not consequences[0]:
                continue
            if p["scope"] == "transcript_consequence":
                p.update(annotation_id=c["annotation_id"], transcript_id=c["Feature"], gene_id=c["gene_id"])
            groups.setdefault(p["group"], []).append(p)
    frequency = one("SELECT * FROM web_variant.variant_frequency WHERE variant_id=:id", params) or {}
    populations = [{"population": pop, "af": frequency.get("AF_exomes_" + pop), "ac": frequency.get("AC_exomes_" + pop),
                    "an": frequency.get("AN_exomes_" + pop), "homozygotes": frequency.get("nhomalt_exomes_" + pop)}
                   for pop in ("afr", "amr", "asj", "eas", "fin", "mid", "nfe", "remaining", "sas")]
    populations.append({"population":"grpmax","af":frequency.get("AF_exomes_grpmax"),
                        "ac":frequency.get("AC_exomes_grpmax"),"an":frequency.get("AN_exomes_grpmax"),
                        "homozygotes":frequency.get("nhomalt_exomes_grpmax"),
                        "selected_ancestry_group":frequency.get("grpmax_exomes")})
    source_rows = query("SELECT source,native_id,alt_index,details_json FROM web_variant.variant_source_detail WHERE variant_id=:id AND source IN ('ClinVar','COSMIC','gnomAD') ORDER BY source,record_id LIMIT 101", params)
    sources = []
    for row in source_rows[:100]:
        data = row["details_json"] or {}
        if row["source"] == "ClinVar":
            selected = fields(data, ["ClinicalSignificance", "ReviewStatus", "Origin", "PhenotypeList", "PhenotypeIDS", "Oncogenicity", "ReviewStatusOncogenicity", "SomaticClinicalImpact", "ReviewStatusClinicalImpact", "NumberSubmitters", "RCVaccession", "SCVsForAggregateGermlineClassification", "SCVsForAggregateSomaticClinicalImpact", "SCVsForAggregateOncogenicityClassification"])
            url = "https://www.ncbi.nlm.nih.gov/clinvar/variation/" + (row["native_id"] or "") + "/"
        elif row["source"] == "COSMIC":
            info = dict(piece.split("=", 1) for piece in data.get("INFO", "").split(";") if "=" in piece)
            selected = fields(info, ["GENE", "TRANSCRIPT", "CDS", "AA", "HGVSC", "HGVSP", "GENOME_SCREEN_SAMPLE_COUNT", "SO_TERM", "LEGACY_ID"]) + fields(data, ["FILTER", "QUAL"])
            url = "https://cancer.sanger.ac.uk/cosmic/search?q=" + (row["native_id"] or "")
        else:
            selected = fields(data, ["FILTER", "QUAL"])
            url = "https://gnomad.broadinstitute.org/variant/" + "-".join(variant_id.split(":")[1:]) + "?dataset=gnomad_r4"
        sources.append({"source": row["source"], "source_id": row["native_id"], "alt_index": row["alt_index"], "url": url, "fields": selected})
    ddg = query('''SELECT d.annotation_id,d.gene_id,d.accession,d.sequence_id,d.position,d.ref_aa,d.alt_aa,d.ddg_pred,d.model,d.checkpoint
        FROM web_variant.variant_ddg_detail d WHERE d.variant_id=:id''' + (" AND d.accession=:accession" if accession else "") + " ORDER BY d.annotation_id,d.prediction_id", params)
    for prediction in ddg:
        # The current published workflow preserves the default ThermoMPNN output
        # without rescaling or sign reversal. Do not infer metadata for other models.
        checkpoint = prediction.pop("checkpoint", None)
        known_model = prediction["model"] == "ThermoMPNN" and checkpoint == "thermoMPNN_default.pt"
        prediction["unit"] = "kcal/mol" if known_model else None
        prediction["effect_convention"] = (
            "Negative values predict stabilization; positive values predict destabilization. "
            "Original ThermoMPNN mutant-minus-wild-type output; no classification threshold is applied."
        ) if known_model else None
    ddg_status = query("SELECT gene_id,annotation_id,sequence_status,prediction_status FROM web_variant.variant_ddg_status WHERE variant_id=:id" + (" AND gene_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)" if accession else ""), params)
    projected = []
    for c in consequences:
        sequence = sequence_status.get(c['gene_id'])
        same_representative = bool(sequence and c['Feature'] in (sequence['transcript_id'], sequence['transcript_stable_id'])
                                   and c['ENSP'] in (sequence['protein_id'], sequence['protein_stable_id'])
                                   and c['selection_method'] == sequence['selection_method'])
        sequence_relation = ({'comparison_status': sequence['comparison_status'], 'status_reason': sequence['status_reason'],
                              'input_sequence_status': sequence['input_sequence_status'], 'input_sequence_source': sequence['input_sequence_source'],
                              'input_sequence_length': sequence['input_sequence_length'], 'comparison_method': sequence['comparison_method'],
                              'exact_matches': exact_targets.get(c['gene_id'], [])} if same_representative else
                             {'comparison_status': 'representative_identity_mismatch' if sequence else 'status_unavailable', 'exact_matches': []})
        projected.append({"annotation_id": c["annotation_id"], "gene_id": c["gene_id"], "transcript_id": c["Feature"], "protein_id": c["ENSP"],
                          "hgvsp": c["HGVSp"], "hgvsc": c["HGVSc"], "consequence": c["Consequence"], "selection_method": c["selection_method"],
                          "canonical_raw":c['CANONICAL'],"feature_type":c['Feature_type'],"transcript_status":classify_transcript(c['Feature_type'],c['Feature'],c['CANONICAL']),
                          "mapping_status": c["mapping_status"], "sequence_relation": sequence_relation,
                          "fields": fields(c, ["IMPACT", "BIOTYPE", "EXON", "INTRON", "Protein_position", "Amino_acids", "Codons", "MANE_SELECT", "MANE_PLUS_CLINICAL", "CANONICAL", "TSL", "APPRIS"] )})
    return {"variant": {"variant_id": variant_id, "chromosome": variant["chrom"], "position": variant["pos"], "ref": variant["ref"], "alt": variant["alt"], "assembly": "GRCh38"},
            "consequences": projected, "prediction_groups": [{"name": k, "items": v} for k, v in groups.items()],
            "frequencies": {"af": frequency.get("AF_exomes"), "ac": frequency.get("AC_exomes"), "an": frequency.get("AN_exomes"),
                            "status": frequency.get("frequency_status", "no_local_frequency_record"), "populations": populations, "source": "gnomAD exomes 4.1", "filters": frequency.get("filters_json")},
            "sources": sources, "sources_has_more": len(source_rows) > 100, "ddg": ddg, "ddg_status": ddg_status,
            "notes": ["Predictions retain original scales; they are not clinical diagnoses.", "Selected MANE transcript does not imply canonical UniProt sequence identity."]}


from .variant_summary import router as variant_summary_router
router.include_router(variant_summary_router)
from .evidence_context import router as context_router
from .evidence_disease import router as disease_router
router.include_router(context_router)
router.include_router(disease_router)

from .evidence_summaries import router as summary_router
router.include_router(summary_router)

from .feature_detail import router as feature_router
router.include_router(feature_router)

from .disease_ptmd import router as ptmd_router
router.include_router(ptmd_router)

from .membrane_overview import router as membrane_overview_router
router.include_router(membrane_overview_router)
