"""Original gene–disease assertions and on-demand HPO evidence."""
from collections import defaultdict
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Query
from .db import query, one
from .evidence_common import require_protein, cursor_read, cursor_write, fields
from .variant_support import amino_change, canonical_rows, protein_identity

router = APIRouter()
PROJECTION = "e.evidence_id,e.disease_id,coalesce(d.name,e.disease_name_raw) name,e.source,e.classification,e.inheritance,e.relationship_status,e.report_url"


def split_source_list(value):
    return list(dict.fromkeys(token.strip() for token in (value or '').split('|') if token.strip() not in ('', '-')))


def clinvar_snv_relation_available():
    # The candidate API remains usable until the validated five-table service
    # projection is imported; do not read unvalidated run-local Parquet.
    return bool(one("SELECT to_regclass('web_clinvar_snv.variant_rcv') IS NOT NULL AS available")['available'])


def clinvar_rcv_for_page(page):
    if not page or not clinvar_snv_relation_available():
        return None
    params = {'ids': sorted({row['variant_id'] for row in page}),
              'source_ids': sorted({row['record_id'] for row in page})}
    approved = query('''SELECT v.variant_id,v.source_row_id,v.allele_id,v.variation_id,
        v.rcv_id,v.rcv_version,v.version_basis,r.trait_set_id,r.trait_set_type,
        r.rcv_status,r.assertion_type,r.germline_classification,r.germline_review_status,
        r.somatic_clinical_impact,r.somatic_review_status,r.oncogenicity_classification,
        r.oncogenicity_review_status,r.no_classification,r.no_classification_review_status,
        r.source_dated
        FROM web_clinvar_snv.variant_rcv v JOIN web_clinvar_snv.rcv r
        USING(rcv_id,rcv_version,variation_id)
        WHERE v.variant_id=ANY(:ids) AND v.source_row_id=ANY(:source_ids)
        ORDER BY v.variant_id,v.source_row_id,v.rcv_id,v.rcv_version''', params)
    if not approved:
        return {}
    rcv_ids = sorted({row['rcv_id'] for row in approved})
    members = query('''SELECT rcv_id,rcv_version,variation_id,trait_set_id,member_index,
        trait_id,trait_type,names_json,xrefs_json
        FROM web_clinvar_snv.rcv_condition_member WHERE rcv_id=ANY(:rcv_ids)
        ORDER BY rcv_id,rcv_version,variation_id,member_index''', {'rcv_ids': rcv_ids})
    scvs = query('''SELECT v.variant_id,v.source_row_id,v.allele_id,v.variation_id,
        v.rcv_id,v.rcv_version,v.scv_id,v.scv_version,v.summary_referenced_by_id,
        v.summary_fields,v.summary_version_status,s.submitter,s.org_id,
        s.record_status,s.assertion_type,s.germline_classification,
        s.somatic_clinical_impact,s.oncogenicity_classification,
        s.review_status,s.date_last_evaluated
        FROM web_clinvar_snv.variant_scv v JOIN web_clinvar_snv.scv s
        USING(rcv_id,rcv_version,variation_id,scv_id,scv_version)
        WHERE v.variant_id=ANY(:ids) AND v.source_row_id=ANY(:source_ids)
        ORDER BY v.variant_id,v.source_row_id,v.rcv_id,v.scv_id,v.scv_version''', params)
    allowed = {(row['variant_id'], row['record_id'], row['variation_id'], row['allele_id']) for row in page}
    member_by_rcv = defaultdict(list)
    for member in members:
        member_by_rcv[(member['rcv_id'], member['rcv_version'], member['variation_id'])].append(member)
    scv_by_rcv = defaultdict(list)
    for scv in scvs:
        key = (scv['variant_id'], scv['source_row_id'], scv['variation_id'], scv['allele_id'])
        if key in allowed:
            scv_by_rcv[(key, scv['rcv_id'], scv['rcv_version'])].append(scv)
    result = defaultdict(list)
    for rcv in approved:
        key = (rcv['variant_id'], rcv['source_row_id'], rcv['variation_id'], rcv['allele_id'])
        if key not in allowed:
            continue
        rcv['condition_members'] = member_by_rcv[(rcv['rcv_id'], rcv['rcv_version'], rcv['variation_id'])]
        rcv['scv_records'] = scv_by_rcv[(key, rcv['rcv_id'], rcv['rcv_version'])]
        result[key].append(rcv)
    return result


@lru_cache(maxsize=16)
def clinvar_condition_rows(accession):
    """Current-SNV ClinVar summary rows; no condition-level classification is inferred."""
    require_protein(accession)
    return query('''WITH ids AS MATERIALIZED (
        SELECT DISTINCT c.variant_id FROM web_variant.variant_consequence c
        WHERE c.gene_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession))
        SELECT l.variant_id,r.record_id,r.native_id,d.version source_version,
          v.chrom,v.pos,v.ref,v.alt,
          r.details_json->>'#AlleleID' allele_id,r.details_json->>'VariationID' variation_id,
          r.details_json->>'PhenotypeList' condition_names,r.details_json->>'PhenotypeIDS' condition_ids,
          r.details_json->>'Origin' origin,r.details_json->>'OriginSimple' origin_simple,
          r.details_json->>'ClinicalSignificance' germline_summary,
          r.details_json->>'ReviewStatus' germline_review_status,
          r.details_json->>'SomaticClinicalImpact' somatic_clinical_impact,
          r.details_json->>'ReviewStatusClinicalImpact' somatic_review_status,
          r.details_json->>'Oncogenicity' oncogenicity,
          r.details_json->>'ReviewStatusOncogenicity' oncogenicity_review_status,
          r.details_json->>'RCVaccession' rcv_accessions,
          r.details_json->>'SCVsForAggregateGermlineClassification' germline_scvs,
          r.details_json->>'SCVsForAggregateSomaticClinicalImpact' somatic_scvs,
          r.details_json->>'SCVsForAggregateOncogenicityClassification' oncogenicity_scvs
        FROM ids JOIN web_variant.variant_source_link l USING(variant_id)
        JOIN web_variant.variant_source_record r USING(record_id)
        JOIN web_variant.variant_dataset d USING(dataset_id)
        JOIN web_variant.variant v USING(variant_id)
        WHERE d.source='ClinVar' AND char_length(v.ref)=1 AND char_length(v.alt)=1
          AND coalesce(r.details_json->>'Type','single nucleotide variant')='single nucleotide variant'
        ORDER BY r.record_id''', {'accession': accession})


def clinvar_condition_groups(accession):
    grouped = defaultdict(list)
    for row in clinvar_condition_rows(accession):
        grouped[(row['condition_names'] or '', row['condition_ids'] or '')].append(row)
    result = []
    for (names, identifiers), rows in grouped.items():
        result.append({
            'condition_set_id': rows[0]['record_id'],
            'condition_names': split_source_list(names) or ['Condition not supplied by the current summary'],
            # Identifier groups retain the source separators and are deliberately
            # not position-paired to names without an RCV-level current asset.
            'identifier_groups': split_source_list(identifiers),
            'variant_count': len({row['variant_id'] for row in rows}),
            'source_record_count': len(rows),
            'origins': sorted({row['origin_simple'] or row['origin'] for row in rows if row['origin_simple'] or row['origin']}),
            'evidence_status': 'current_summary_condition_set',
        })
    result.sort(key=lambda item: (-item['variant_count'], ' | '.join(item['condition_names']).casefold(), item['condition_set_id']))
    return result


@router.get('/proteins/{accession}/diseases/clinvar-conditions')
def clinvar_conditions(accession: str, search: str = Query('', max_length=200),
                       limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=100000)):
    groups = clinvar_condition_groups(accession)
    total_variants = len({row['variant_id'] for row in clinvar_condition_rows(accession)})
    if search:
        term = search.casefold()
        groups = [group for group in groups if term in ' '.join(group['condition_names'] + group['identifier_groups']).casefold()]
    page = groups[offset:offset + limit]
    versions = sorted({row['source_version'] for row in clinvar_condition_rows(accession)})
    formal = clinvar_snv_relation_available()
    return {
        'items': page,
        'totals': {'condition_sets': len(clinvar_condition_groups(accession)), 'variants': total_variants,
                   'source_records': len(clinvar_condition_rows(accession))},
        'filtered_condition_sets': len(groups), 'offset': offset, 'limit': limit,
        'next_offset': offset + limit if offset + limit < len(groups) else None,
        'source': {'name': 'ClinVar variant_summary', 'versions': versions, 'evidence_level': 'summary_condition_set'},
        'formal_relation_available': formal,
        'notes': [
            'Condition names and identifier groups are retained exactly as a source condition set; names are not merged across records.',
            'RCV/SCV evidence is attached only to an exact current-SNV source row and VariationID/AlleleID pair; RCV classification remains on its full condition set.' if formal else 'The current summary does not resolve RCV/SCV versions or map each aggregate classification/submission to an individual condition member.',
            'Variation-level germline, somatic-impact and oncogenicity summaries are shown only on their source variant record and are not condition classifications.',
        ],
    }


@router.get('/proteins/{accession}/diseases/clinvar-conditions/{condition_set_id}')
def clinvar_condition_detail(accession: str, condition_set_id: str,
                             limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0, le=100000)):
    rows = clinvar_condition_rows(accession)
    anchor = next((row for row in rows if row['record_id'] == condition_set_id), None)
    if not anchor:
        raise HTTPException(404, 'ClinVar condition set not found for this protein')
    matching = [row for row in rows if (row['condition_names'] or '', row['condition_ids'] or '') ==
                (anchor['condition_names'] or '', anchor['condition_ids'] or '')]
    page = matching[offset:offset + limit]
    formal_relations = clinvar_rcv_for_page(page)
    ids = list({row['variant_id'] for row in page})
    changes = query('''SELECT DISTINCT ON (c.variant_id) c.variant_id,c.annotation_id,c.gene_id,c."HGVSp" hgvsp
        FROM web_variant.variant_consequence c WHERE c.variant_id=ANY(:ids)
          AND c.gene_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)
        ORDER BY c.variant_id,c.annotation_id,c.gene_id''', {'ids': ids, 'accession': accession}) if ids else []
    change_by_variant = {row['variant_id']: row for row in changes}
    sequence = protein_identity(accession)['sequence_id']
    mapped = canonical_rows(ids, sequence)
    positions = defaultdict(list)
    for row in mapped:
        value = {key: row[key] for key in ('sequence_id', 'position', 'ref_aa', 'alt_aa')}
        if value not in positions[row['variant_id']]:
            positions[row['variant_id']].append(value)
    items = []
    for row in page:
        consequence = change_by_variant.get(row['variant_id'], {})
        relation_key = (row['variant_id'], row['record_id'], row['variation_id'], row['allele_id'])
        rcv_records = formal_relations.get(relation_key, []) if formal_relations is not None else []
        summary_rcv = split_source_list(row['rcv_accessions'])
        items.append({
            'variant_id': row['variant_id'], 'chromosome': row['chrom'], 'position': row['pos'],
            'ref': row['ref'], 'alt': row['alt'], 'source_record_id': row['record_id'],
            'variation_id': row['variation_id'] or row['native_id'], 'allele_id': row['allele_id'],
            'transcript_change': amino_change(consequence.get('hgvsp')),
            'canonical_positions': positions[row['variant_id']],
            'origin': row['origin'],
            'variation_summary': {
                'germline_classification': row['germline_summary'], 'germline_review_status': row['germline_review_status'],
                'somatic_clinical_impact': row['somatic_clinical_impact'], 'somatic_review_status': row['somatic_review_status'],
                'oncogenicity': row['oncogenicity'], 'oncogenicity_review_status': row['oncogenicity_review_status'],
                'scope': 'variation_summary_not_condition_specific',
            },
            'rcv_accessions': summary_rcv,
            'rcv_records': rcv_records,
            'scv_accessions': {
                'germline': split_source_list(row['germline_scvs']),
                'somatic_clinical_impact': split_source_list(row['somatic_scvs']),
                'oncogenicity': split_source_list(row['oncogenicity_scvs']),
            },
            'clinvar_url': 'https://www.ncbi.nlm.nih.gov/clinvar/variation/' + str(row['variation_id'] or row['native_id']) + '/',
            'condition_link_status': ('awaiting_formal_curated_import' if formal_relations is None else
                                      'approved_rcv_link' if rcv_records else
                                      'summary_no_rcv_accession' if not summary_rcv else 'no_approved_rcv_link'),
        })
    return {
        'condition_set_id': condition_set_id,
        'condition_names': split_source_list(anchor['condition_names']) or ['Condition not supplied by the current summary'],
        'identifier_groups': split_source_list(anchor['condition_ids']),
        'source_version': anchor['source_version'], 'items': items, 'total_variants': len(matching),
        'next_offset': offset + limit if offset + limit < len(matching) else None,
        'evidence_status': 'current_summary_condition_set_with_rcv_scv' if formal_relations is not None else 'current_summary_condition_set_only',
        'notes': [
            'RCV classifications apply to the intact source TraitSet; split members are navigation, not independent classifications.' if formal_relations is not None else 'RCV and SCV accessions are retained on the variation summary record but are not assigned to individual condition members here.',
            'Only canonical_positions are verified against the current UniProt sequence; transcript_change remains in the selected transcript context.',
            'Germline classification, somatic clinical impact and oncogenicity remain separate variation-level source fields.',
        ],
    }


@router.get("/proteins/{accession}/diseases")
def diseases(accession: str, source: str = "", limit: int = Query(20, ge=1, le=100), cursor: str = "", offset: int = Query(0, ge=0)):
    require_protein(accession)
    context = ["diseases", accession, source]
    after = cursor_read(cursor, context) or ""
    params = {"accession": accession, "source": source, "after": after, "limit": limit + 1, "offset": 0 if cursor else offset}
    rows = query(f'''SELECT {PROJECTION},e.submitter FROM web_disease.protein_disease_evidence e
        LEFT JOIN web_disease.disease_entry d USING(disease_id)
        WHERE e.accession=:accession AND e.evidence_id>:after''' + (" AND e.source=:source" if source else "") +
        " ORDER BY e.evidence_id LIMIT :limit OFFSET :offset", params)
    sources = query("SELECT DISTINCT source FROM web_disease.protein_disease_evidence WHERE accession=:accession ORDER BY source", params)
    dosage = query('''SELECT gene_id,gene_symbol,haploinsufficiency,triplosensitivity,report_url
        FROM web_disease.gene_dosage WHERE gene_id IN (SELECT gene_id FROM web_disease.gene_protein_link WHERE accession=:accession)''', params)
    return {"items": rows[:limit], "next_cursor": cursor_write(rows[limit - 1]["evidence_id"], context) if len(rows) > limit else None,
            "filters": {"sources": [r["source"] for r in sources]}, "gene_dosage": dosage,
            "note": "Gene–disease assertions retain each source's evidence. They do not assert that all variants cause the disease."}


@router.get("/diseases/{disease_id}")
def disease_detail(disease_id: str, accession: str = "", limit: int = Query(30, ge=1, le=100), cursor: str = "", offset: int = Query(0, ge=0)):
    disease = one("SELECT disease_id,name,definition,definition_source,source_url,is_obsolete,mondo_mapping_status FROM web_disease.disease_entry_detail WHERE disease_id=:id", {"id": disease_id})
    if not disease:
        raise HTTPException(404, "Disease not found")
    context = ["phenotypes", disease_id, accession]
    after = cursor_read(cursor, context) or ""
    params = {"id": disease_id, "accession": accession, "after": after, "limit": limit + 1, "offset": 0 if cursor else offset}
    evidence = query(f'''SELECT {PROJECTION},e.gene_id,e.submitter,e.references,e.phenotype_raw,e.mapping_key
        FROM web_disease.gene_disease_evidence_detail e LEFT JOIN web_disease.disease_entry d USING(disease_id)
        WHERE e.disease_id=:id''' + (" AND e.gene_id IN (SELECT gene_id FROM web_disease.gene_protein_link WHERE accession=:accession)" if accession else "") +
        " ORDER BY e.source,e.evidence_id LIMIT 101", params)
    phenotypes = query('''SELECT p.annotation_id,p.hpo_id,p.resolved_hpo_id,t.name,p.qualifier,p.evidence,p.frequency,p.onset,p.sex,p.reference,p.modifier,p.aspect,p.phenotype_status
        FROM web_disease.disease_phenotype p LEFT JOIN web_disease.ontology_term t ON t.term_id=p.resolved_hpo_id
        WHERE p.disease_id=:id AND p.annotation_id>:after ORDER BY p.annotation_id LIMIT :limit OFFSET :offset''', params)
    return {"disease": disease, "evidence": evidence[:100], "evidence_has_more": len(evidence) > 100,
            "phenotypes": phenotypes[:limit], "next_cursor": cursor_write(phenotypes[limit - 1]["annotation_id"], context) if len(phenotypes) > limit else None,
            "notes": ["NOT qualifiers remain explicit; absent evidence is not a negative finding.", "MONDO mappings retain their original mapping status."]}
