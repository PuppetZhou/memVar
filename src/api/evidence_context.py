"""Source-aware PPI, expression and QTL projections with bounded pagination."""
import re
import math
from functools import lru_cache
from statistics import median
from fastapi import APIRouter, HTTPException, Query
from .db import query, one
from .evidence_common import require_protein, cursor_read, cursor_write, fields, clean

router = APIRouter()
PPI_FULL = "EXISTS (SELECT 1 FROM web_context.ppi_membership m JOIN web_context.context_dataset d USING(dataset_id) WHERE m.record_id=i.record_id AND d.kind IN ('biogrid_full','intact_full') LIMIT 1 OFFSET 0)"
PPI_TYPE = "coalesce(i.details_json->>'Experimental System Type',i.details_json->>'Interaction type(s)',i.details_json->>'Feature type')"
PPI_METHOD = "coalesce(i.details_json->>'Experimental System',i.details_json->>'Interaction detection method(s)')"


def qtl_source_assessment(source, row):
    """Display source statistics without filtering or assigning gene q-values to pairs."""
    def probability(raw):
        try:
            value = float(raw) if raw is not None and not isinstance(raw, bool) else float('nan')
        except (TypeError, ValueError):
            return None
        return value if math.isfinite(value) and 0 <= value <= 1 else None

    if source == 'GTEx':
        value, threshold = probability(row.get('pval_nominal')), probability(row.get('pval_nominal_threshold'))
        metric, operator = 'Nominal P', '≤'
        basis = 'GTEx tissue / phenotype-specific nominal P threshold; official significant-pairs collection'
    elif source == 'eQTLGen':
        value, threshold = probability(row.get('FDR')), 0.05
        metric, operator = 'FDR', '<'
        basis = 'eQTLGen source FDR < 0.05'
    else:
        value, threshold, metric, operator = None, None, None, None
        basis = 'No harmonized source significance criterion supplied'
    status = 'unavailable'
    if value is not None and threshold is not None:
        passed = value <= threshold if operator == '≤' else value < threshold
        status = 'met' if passed else 'not_met'
    return dict(status=status, metric=metric, value=value, threshold=threshold,
                operator=operator, basis=basis)


def short_mi(value):
    if not value:
        return None
    parts = re.findall(r'\(([^()]*)\)', value)
    return " / ".join(dict.fromkeys(parts)) if parts else value


def publications(raw):
    return [{"id": "PMID:" + v, "url": "https://pubmed.ncbi.nlm.nih.gov/" + v + "/"}
            for v in dict.fromkeys(re.findall(r'pubmed:(\d+)', raw or '', re.I))]


PPI_KINDS = ('biogrid_full', 'intact_full', 'biogrid_context', 'intact_context', 'intact_mutation')


def ppi_type_name(raw):
    # Mutation files use label(MI:xxxx), unlike MITAB's MI:xxxx(label).
    if raw and re.search(r'\(MI:\d+\)$', raw):
        return re.sub(r'\(MI:\d+\)$', '', raw).strip()
    return short_mi(raw)


def ppi_scope(dataset):
    if not dataset:
        return PPI_FULL
    entry = one("SELECT kind FROM web_context.context_dataset WHERE dataset_id=:dataset", {'dataset': dataset})
    if not entry or entry['kind'] not in PPI_KINDS:
        raise HTTPException(422, 'Choose a known PPI collection.')
    return "EXISTS(SELECT 1 FROM web_context.ppi_membership m WHERE m.record_id=i.record_id AND m.dataset_id=:dataset)"


@lru_cache(maxsize=128)
def ppi_collections(accession):
    return query('''WITH matched AS MATERIALIZED (
        SELECT DISTINCT record_id FROM web_context.ppi_protein_link WHERE target_accession=:accession),
        counts AS (SELECT m.dataset_id,count(DISTINCT m.record_id) records FROM matched
            JOIN web_context.ppi_membership m USING(record_id) GROUP BY m.dataset_id)
        SELECT d.dataset_id,d.provider source,d.kind,d.details_json->>'context_raw' context,
            d.details_json->>'source_release' source_release,coalesce(c.records,0) records
        FROM web_context.context_dataset d LEFT JOIN counts c USING(dataset_id)
        WHERE d.kind=ANY(:kinds) ORDER BY d.provider,d.kind,d.dataset_id''',
        {'accession': accession, 'kinds': list(PPI_KINDS)})


@lru_cache(maxsize=256)
def ppi_filter_rows(accession, dataset=''):
    scope = ppi_scope(dataset)
    return query(f'''SELECT DISTINCT i.provider,{PPI_TYPE} raw_type,{PPI_METHOD} raw_method FROM web_context.ppi_interaction i
        WHERE EXISTS (SELECT 1 FROM web_context.ppi_protein_link l WHERE l.record_id=i.record_id AND l.target_accession=:accession)
        AND {scope} ORDER BY i.provider,raw_type,raw_method''', {'accession': accession, 'dataset': dataset})


@lru_cache(maxsize=512)
def ppi_filters(accession, dataset='', source='', interaction_type=''):
    rows = ppi_filter_rows(accession, dataset)
    scoped = [row for row in rows if not source or row['provider'] == source]
    if interaction_type:
        scoped_for_methods = [row for row in scoped if row['raw_type'] and
                              row['provider'] + ': ' + ppi_type_name(row['raw_type']) == interaction_type]
    else:
        scoped_for_methods = scoped
    return {
        'sources': sorted({row['provider'] for row in rows}),
        'interaction_types': sorted({row['provider'] + ': ' + ppi_type_name(row['raw_type']) for row in scoped if row['raw_type']}),
        'detection_methods': sorted({row['provider'] + ': ' + (short_mi(row['raw_method']) or row['raw_method'])
                                     for row in scoped_for_methods if row['raw_method']}),
    }


def participant(row):
    data = row["details_json"] or {}
    e = row["endpoint"]
    identity = clean(data.get("#ID(s) interactor " + e)) or clean(data.get("ID(s) interactor " + e)) or clean(data.get("SWISS-PROT Accessions Interactor " + e)) or clean(data.get("Entrez Gene Interactor " + e))
    aliases = data.get("Alias(es) interactor " + e, "")
    gene = re.search(r'uniprotkb:([^|()]+)\(gene name\)', aliases)
    accession = None
    if identity:
        match = re.search(r'uniprotkb:([A-Z0-9]+(?:-\d+)?)', identity)
        if match:
            accession = match.group(1)
        elif re.fullmatch(r'[A-Z][A-Z0-9]{5,9}(?:-\d+)?', identity):
            accession = identity
    return {"endpoint": e, "name": clean(data.get("Official Symbol Interactor " + e)) or (gene.group(1) if gene else None) or identity,
            "identifier": identity, "accession": accession,
            "taxon": clean(data.get("Organism Name Interactor " + e)) or short_mi(data.get("Taxid interactor " + e)),
            "object_type": short_mi(data.get("Type(s) interactor " + e)) or ("protein" if accession else "source participant"),
            "fields": fields(data, ["Biological role(s) interactor " + e, "Experimental role(s) interactor " + e,
                                     "Feature(s) interactor " + e, "Annotation(s) interactor " + e, "Stoichiometry(s) interactor " + e])}


def mark_project_participants(participants):
    accessions = list({p["accession"] for p in participants if p.get("accession")})
    known = {r["accession"] for r in query("SELECT accession FROM web.protein WHERE accession=ANY(:ids)", {"ids": accessions})} if accessions else set()
    for p in participants:
        p["project_entry"] = p.get("accession") in known


def ppi_project(row, participants, own_endpoints):
    data = row["details_json"]
    if 'Affected protein AC' in data:
        pmids = re.findall(r'(?<!\d)\d{4,10}(?!\d)', data.get('PubMedID') or '')
        return {'record_id': row['record_id'], 'record_kind': 'mutation', 'source': row['provider'],
                'partners': [], 'interaction_type': ppi_type_name(data.get('Feature type')),
                'detection_method': None, 'negative': None, 'non_protein_participant': None,
                'source_id': data.get('Interaction AC'),
                'publications': [{'id': 'PMID:'+p, 'url': 'https://pubmed.ncbi.nlm.nih.gov/'+p+'/'} for p in dict.fromkeys(pmids)],
                'mutation': {key: data.get(field) for key,field in [
                    ('feature_id','#Feature AC'), ('label','Feature short label'), ('feature_type','Feature type'),
                    ('range','Feature range(s)'), ('original','Original sequence'), ('resulting','Resulting sequence'),
                    ('annotation','Feature annotation'), ('affected_protein','Affected protein AC'),
                    ('affected_symbol','Affected protein symbol'), ('participants_raw','Interaction participants'),
                    ('interaction_id','Interaction AC')]},
                'coordinate_status': 'Source coordinates; not validated against the canonical sequence or project variants.'}
    projected = [participant(p) for p in participants]
    partners = [p for p in projected if p["endpoint"] not in own_endpoints] or projected
    return {"record_id": row["record_id"], "record_kind": "interaction", "source": row["provider"], "partners": partners,
            "interaction_type": short_mi(data.get("Experimental System Type") or data.get("Interaction type(s)")),
            "detection_method": short_mi(data.get("Experimental System") or data.get("Interaction detection method(s)")),
            "publications": publications(data.get("Publication Source") or data.get("Publication Identifier(s)")),
            "negative": str(data.get("Negative", "false")).lower() == "true",
            "source_id": data.get("#BioGRID Interaction ID") or data.get("Interaction identifier(s)"),
            "non_protein_participant": any(p["object_type"] not in ("protein", "source participant") for p in projected)}


@router.get("/proteins/{accession}/ppi")
def ppi(accession: str, source: str = "", interaction_type: str = "", detection_method: str = "",
        limit: int = Query(20, ge=1, le=100), cursor: str = "", dataset: str = Query("", max_length=160),
        offset: int = Query(0, ge=0)):
    require_protein(accession)
    context = ["ppi", accession, source, interaction_type, detection_method, dataset]
    after = cursor_read(cursor, context)
    params = dict(accession=accession, source=source, dataset=dataset, after=after or "", limit=limit + 1, offset=0 if cursor else offset)
    conditions = [ppi_scope(dataset)]
    if source:
        conditions.append("i.provider=:source")
    if interaction_type:
        # Keep provider categories separate; no cross-source equivalence is inferred.
        raw_types = ppi_filter_rows(accession, dataset)
        selected = [(r["provider"], r["raw_type"]) for r in raw_types if r["raw_type"] and r["provider"] + ": " + ppi_type_name(r["raw_type"]) == interaction_type]
        if not selected:
            return {"items": [], "next_cursor": None, "filters": ppi_filters(accession, dataset, source, interaction_type)}
        params.update(type_provider=selected[0][0], raw_types=[r[1] for r in selected])
        conditions.append(f"i.provider=:type_provider AND {PPI_TYPE}=ANY(:raw_types)")
    if detection_method:
        raw_methods = ppi_filter_rows(accession, dataset)
        selected = [(r['provider'], r['raw_method']) for r in raw_methods if r['raw_method'] and
                    r['provider'] + ': ' + (short_mi(r['raw_method']) or r['raw_method']) == detection_method and
                    (not interaction_type or (r['raw_type'] and r['provider'] + ': ' + ppi_type_name(r['raw_type']) == interaction_type))]
        if not selected:
            return {"items": [], "next_cursor": None, "filters": ppi_filters(accession, dataset, source, interaction_type)}
        params.update(method_provider=selected[0][0], raw_methods=list({row[1] for row in selected}))
        conditions.append(f"i.provider=:method_provider AND {PPI_METHOD}=ANY(:raw_methods)")
    rows = query('''WITH matched AS MATERIALIZED (
        SELECT DISTINCT record_id FROM web_context.ppi_protein_link
        WHERE target_accession=:accession AND record_id>:after),
        linked AS MATERIALIZED (SELECT i.record_id,i.provider,i.details_json FROM matched m
            JOIN web_context.ppi_interaction i USING(record_id))
        SELECT i.record_id,i.provider,i.details_json FROM linked i WHERE ''' + " AND ".join(conditions) + " ORDER BY i.record_id LIMIT :limit OFFSET :offset", params)
    page = rows[:limit]
    ids = [r["record_id"] for r in page]
    participants = query("SELECT record_id,endpoint,details_json FROM web_context.ppi_participant WHERE record_id=ANY(:ids) ORDER BY endpoint", {"ids": ids}) if ids else []
    links = query("SELECT DISTINCT record_id,endpoint FROM web_context.ppi_protein_link WHERE target_accession=:accession AND record_id=ANY(:ids)", {"ids": ids, "accession": accession}) if ids else []
    items = [ppi_project(r, [p for p in participants if p["record_id"] == r["record_id"]],
                         {l["endpoint"] for l in links if l["record_id"] == r["record_id"]}) for r in page]
    mark_project_participants([p for item in items for p in item["partners"]])
    return {"items": items, "next_cursor": cursor_write(page[-1]["record_id"], context) if len(rows) > limit else None,
            "filters": ppi_filters(accession, dataset, source, interaction_type), "scope": "Selected source collection; counts retain source records and overlapping memberships are not independent evidence.", "dataset": dataset}


@router.get("/ppi/{record_id}")
def ppi_detail(record_id: str, accession: str = ""):
    row = one("SELECT * FROM web_context.ppi_interaction WHERE record_id=:id", {"id": record_id})
    if not row:
        raise HTTPException(404, "Interaction not found")
    participants = query("SELECT * FROM web_context.ppi_participant WHERE record_id=:id ORDER BY endpoint", {"id": record_id})
    links = query("SELECT DISTINCT endpoint FROM web_context.ppi_protein_link WHERE record_id=:id AND target_accession=:accession", {"id": record_id, "accession": accession})
    result = ppi_project(row, participants, {r["endpoint"] for r in links})
    result["participants"] = [participant(p) for p in participants]
    result['collections'] = query('''SELECT DISTINCT d.dataset_id,d.provider,d.kind,d.details_json->>'context_raw' context
        FROM web_context.ppi_membership m JOIN web_context.context_dataset d USING(dataset_id)
        WHERE m.record_id=:id ORDER BY d.dataset_id''', {'id': record_id})
    mark_project_participants(result["partners"] + result["participants"])
    result["fields"] = fields(row["details_json"], ["Score", "Confidence value(s)", "Throughput", "Modification", "Qualifications", "Host organism(s)", "Expansion method(s)", "Interaction parameter(s)", "Interaction annotation(s)"])
    result["contexts"] = [r["context"] for r in query("SELECT DISTINCT d.details_json->>'context_raw' context FROM web_context.ppi_membership m JOIN web_context.context_dataset d USING(dataset_id) WHERE m.record_id=:id ORDER BY context", {"id": record_id})]
    if result.get('record_kind') == 'mutation':
        result['fields'] = fields(row['details_json'], list(row['details_json']))
        result['mapping_statuses'] = query("SELECT DISTINCT mutation_coordinate_status FROM web_context.ppi_membership WHERE record_id=:id", {'id': record_id})
    else:
        result["coordinate_status"] = "Participant feature coordinates are source annotations, not validated canonical variant mappings."
    return result


def qtl_datasets(accession):
    return query('''SELECT DISTINCT d.dataset_id,d.provider,d.kind,
        coalesce(d.details_json->>'tissue',d.details_json->>'Tissue',d.details_json->>'background') tissue,
        d.details_json FROM web_context.qtl_context_count c JOIN web_context.context_dataset d USING(dataset_id)
        WHERE c.hgnc_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)
        AND c.table_name <> 'gtex_qtl_summary' ORDER BY d.dataset_id''', {"accession": accession})


@router.get("/proteins/{accession}/qtl")
def qtl(accession: str, source: str = "GTEx", tissue: str = "", qtl_type: str = "",
        limit: int = Query(20, ge=1, le=100), cursor: str = "", offset: int = Query(0, ge=0)):
    require_protein(accession)
    source = source or "GTEx"
    if source not in ("GTEx", "eQTLGen", "QTLbase"):
        raise HTTPException(422, "Unknown QTL source")
    datasets = qtl_datasets(accession)
    available = [d for d in datasets if d["provider"] == source]
    chosen = [d for d in available if (not tissue or d["tissue"] == tissue) and (not qtl_type or d["kind"] == qtl_type)]
    filters = {"sources": sorted({d["provider"] for d in datasets}), "tissues": sorted({d["tissue"] for d in available if d["tissue"]}), "qtl_types": sorted({d["kind"] for d in available})}
    context = ["qtl", accession, source, tissue, qtl_type]
    state = cursor_read(cursor, context)
    if state is None:
        dataset_index = 0
        if offset:
            # Existing gene-scoped published counts locate a global jump without reading skipped associations.
            counts = {r['dataset_id']: r['records'] for r in query('''SELECT dataset_id,sum(record_count)::bigint records
                FROM web_context.qtl_context_count
                WHERE hgnc_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)
                AND table_name IN ('gtex_qtl_pair','eqtlgen_cis','qtlbase_association')
                GROUP BY dataset_id''', {'accession': accession})}
            while dataset_index < len(chosen) and offset >= counts.get(chosen[dataset_index]['dataset_id'], 0):
                offset -= counts.get(chosen[dataset_index]['dataset_id'], 0)
                dataset_index += 1
        state = [dataset_index, offset]
    # Walk source datasets in fixed order instead of sorting hundreds of thousands of gene rows.
    dataset_index, offset = state
    items = []
    while dataset_index < len(chosen) and len(items) <= limit:
        d = chosen[dataset_index]
        table = {"GTEx": "gtex_qtl_pair", "eQTLGen": "eqtlgen_cis", "QTLbase": "qtlbase_association"}[source]
        order = "source_row" if source == "GTEx" else '"SNPChr","SNPPos","SNP",ctid' if source == "eQTLGen" else '"SNP_chr","SNP_pos_hg38","Trait_chr","Trait_start_hg38",ctid'
        # ctid only breaks identical source-row ties within this immutable published snapshot.
        rows = query(f'''SELECT t.* FROM web_context.{table} t WHERE dataset_id=:dataset
            AND hgnc_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)
            ORDER BY {order} LIMIT :limit OFFSET :offset''',
            {"dataset": d["dataset_id"], "accession": accession, "limit": limit + 1 - len(items), "offset": offset})
        for index, row in enumerate(rows):
            item = {"record_id": d["dataset_id"] + ":" + str(offset + index), "source": source,
                    "qtl_type": d["kind"], "tissue": d["tissue"], "assembly": d["details_json"].get("assembly"),
                    "_cursor": [dataset_index, offset + index + 1]}
            if source == "GTEx":
                pieces = row["variant_id"].split("_")
                item.update(variant=row["variant_id"], chromosome=pieces[0], position=pieces[1] if len(pieces) > 1 else None,
                            phenotype=row["phenotype_id"], pvalue=row["pval_nominal"], effect=row["slope"], effect_type="slope",
                            details=fields(row, ["pval_nominal_threshold", "slope_se", "af", "ma_samples", "ma_count", "group_id", "pval_beta", "min_pval_nominal"]))
            elif source == "eQTLGen":
                item.update(variant=row["SNP"], chromosome=row["SNPChr"], position=row["SNPPos"], phenotype=row["Gene"],
                            pvalue=row["Pvalue"], effect=row["Zscore"], effect_type="Zscore",
                            details=fields(row, ["AssessedAllele", "OtherAllele", "FDR", "NrCohorts", "NrSamples", "BonferroniP"]))
            else:
                item.update(variant=row["SNP_chr"] + ":" + (row["SNP_pos_hg38"] or "?"), chromosome=row["SNP_chr"], position=row["SNP_pos_hg38"],
                            assembly="GRCh38 (source hg38)", phenotype=row["Mapped_gene"], pvalue=row["Pvalue"], effect=None, effect_type=None,
                            details=fields(row, ["SNP_pos_hg19", "Trait_chr", "Trait_start_hg19", "Trait_end_hg19", "Trait_start_hg38", "Trait_end_hg38"]) + fields(d["details_json"], ["PMID", "Population", "Sample_size", "Sourceid"]))
            item['source_assessment'] = qtl_source_assessment(source, row)
            items.append(item)
        if len(items) > limit:
            break
        dataset_index += 1
        offset = 0
    next_cursor = cursor_write(items[limit - 1]["_cursor"], context) if len(items) > limit else None
    for item in items:
        item.pop("_cursor", None)
    return {"items": items[:limit], "next_cursor": next_cursor, "filters": filters, "applied_source": source,
            "note": "Source associations retain their assembly and statistics. No variant mapping or new significance threshold is applied."}


# Explicitly selected original measurements; no numerical cross-source normalization.
EXPRESSION = [
    ("rna_tissue_hpa", "HPA", "normal", "nTPM", "nTPM", ["TPM", "pTPM"]),
    ("normal_ihc_data", "HPA", "normal", "Level", "qualitative IHC", ["Reliability"]),
    ("rna_tissue_fantom", "FANTOM", "normal", "Tags per million", "tags per million", ["Scaled tags per million", "Normalized tags per million"]),
    ("ms_tissue_sample_data", "HPA", "normal", "Intensity", "source intensity", []),
    ("cancer_data", "HPA", "cancer", "High", "IHC category counts", ["Medium", "Low", "Not detected"]),
    ("cancer_cptac", "CPTAC", "cancer", "logFC", "logFC", ["p-value adjusted"]),
    ("rna_cancer_sample", "HPA", "cancer", "pTPM", "pTPM", []),
    ("rna_celline", "HPA", "cell_line", "nTPM", "nTPM", ["TPM", "pTPM"]),
    ("rna_cell_line_cancer", "HPA", "cell_line", "nTPM", "nTPM", ["TPM", "pTPM"]),
    ("rna_single_cell_type", "HPA", "single_cell", "nCPM", "nCPM", []),
    ("rna_single_cell_cluster", "HPA", "single_cell", "nCPM", "nCPM", ["Read count"]),
    ("dvp_cell_type", "HPA", "single_cell", "Intensity", "source intensity", []),
    ("dvp_cell_type_group_data", "HPA", "single_cell", "Intensity", "source intensity", ["Matched nCPM"]),
]
GTEX_EXPRESSION = ('gtex_gene_median_tpm', 'GTEx', 'normal', 'median TPM', 'TPM', [])


def expression_spec(dataset):
    for spec in [GTEX_EXPRESSION] + EXPRESSION:
        if spec[0] == dataset:
            return spec
    raise HTTPException(422, 'Choose a known expression dataset')


def expression_context_label(row):
    return row.get('context') or ' · '.join(str(v) for v in (row.get('context_json') or {}).values() if v not in (None, '', '-'))


# These are display groupings over one source dataset and one measurement. They
# never merge sources or units. Only the three sample/cluster datasets below
# receive a project median; source-provided tissue summaries remain source values.
EXPRESSION_MATRIX_GROUPS = {
    'normal_ihc_data': ('Tissue', False),
    'ms_tissue_sample_data': ('Tissue', True),
    'rna_cancer_sample': ('Cancer', True),
    'rna_single_cell_cluster': ('Tissue', True),
}


def numeric_value(value):
    value = clean(value)
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float('inf') else None


@lru_cache(maxsize=24)
def _expression_matrix(accession, dataset):
    require_protein(accession)
    name, provider, category, measurement, unit, extra = expression_spec(dataset)
    params = {'accession': accession}
    if provider == 'GTEx':
        rows = query('''SELECT r.source_gene_id,s.sample_id context_key,s.sample_id context,
            '{}'::jsonb context_json,r.values->>s.sample_index::int primary_value
            FROM web_context.expression_gtex_gene_median_tpm r
            JOIN web_context.expression_gtex_sample s ON s.dataset_id='gtex_expression:gtex_gene_median_tpm'
            WHERE r.hgnc_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)
            ORDER BY r.source_gene_id,s.sample_index''', params)
    else:
        # Identifiers are selected only through expression_spec's fixed contract.
        rows = query(f'''SELECT r.*,r."{measurement}" primary_value FROM web_context.expression_{name}_detail r
            WHERE r.hgnc_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)
            ORDER BY r.source_gene_id,r.context_id''', params)
    group_field, project_median = EXPRESSION_MATRIX_GROUPS.get(name, (None, False))
    groups = {}
    all_numeric = []
    categories = set()
    for index, row in enumerate(rows):
        context = row.get('context_json') or {}
        context_label = expression_context_label(row)
        group_label = str(context.get(group_field) or context_label) if group_field else context_label
        sample_label = next((str(context[key]) for key in ('Sample', 'sample_name', 'Cluster', 'Cell type', 'Cell type name', 'Cell line', 'replicate_nr')
                             if context.get(key) not in (None, '', '-')), context_label)
        raw_value = clean(row.get('primary_value'))
        numeric = numeric_value(raw_value)
        if numeric is None and raw_value is not None:
            categories.add(str(raw_value))
        elif numeric is not None:
            all_numeric.append(numeric)
        detail_fields = [{'label': key, 'value': value} for key, value in context.items() if value not in (None, '', '-')]
        detail_fields += fields(row, extra)
        item = {
            'record_id': f'{name}:{row.get("source_gene_id")}:{row.get("context_key", row.get("context_id", index))}',
            'context_key': str(row.get('context_key', row.get('context_id', index))),
            'source': provider, 'category': category, 'dataset': name,
            'context': context_label, 'group': group_label, 'sample': sample_label,
            'measurement': measurement, 'value': raw_value, 'numeric_value': numeric,
            'unit': unit, 'details': detail_fields,
        }
        groups.setdefault(group_label, []).append(item)
    projected_groups = []
    for group_label, items in groups.items():
        values = [item['numeric_value'] for item in items if item['numeric_value'] is not None]
        available = [item for item in items if item['value'] is not None]
        projected_groups.append({
            'key': group_label, 'label': group_label, 'records': len(items),
            'available_values': len(available), 'missing_values': len(items) - len(available),
            'median': median(values) if project_median and values else None,
            'summary_kind': 'project_median' if project_median and values else 'source_values',
            'items': items,
        })
    projected_groups.sort(key=lambda group: (-group['records'], group['label'].casefold()))
    nonnegative_rna = (name == 'gtex_gene_median_tpm' or name.startswith('rna_')) and all(value >= 0 for value in all_numeric)
    if measurement == 'Level' or (categories and not all_numeric):
        scale_kind = 'categorical'
    elif measurement == 'logFC':
        scale_kind = 'diverging'
    elif nonnegative_rna:
        scale_kind = 'log1p'
    else:
        scale_kind = 'linear'
    return {
        'dataset': name, 'source': provider, 'category': category,
        'measurement': measurement, 'unit': unit,
        'groups': projected_groups,
        'totals': {'records': len(rows), 'groups': len(projected_groups),
                   'available_values': sum(group['available_values'] for group in projected_groups),
                   'missing_values': sum(group['missing_values'] for group in projected_groups)},
        'scale': {'kind': scale_kind,
                  'minimum': min(all_numeric) if all_numeric else None,
                  'maximum': max(all_numeric) if all_numeric else None,
                  'maximum_absolute': max((abs(value) for value in all_numeric), default=None),
                  'categories': sorted(categories)},
        'project_summary': 'median_in_original_units' if project_median else None,
        'notes': [
            'Every cell is an original value from the selected source dataset; missing values are not zero.',
            'Project medians, when present, are calculated within the displayed source, measurement, unit and source-defined group.',
            'log1p changes only the colour scale for non-negative RNA measurements; displayed and detail values remain in original units.',
        ],
    }


@router.get('/proteins/{accession}/expression/matrix')
def expression_matrix(accession: str, dataset: str = Query(..., min_length=1, max_length=100)):
    return _expression_matrix(accession, dataset)


@router.get("/proteins/{accession}/expression")
def expression(accession: str, source: str = "", category: str = "normal", limit: int = Query(30, ge=1, le=100), cursor: str = "", dataset: str = "", context_key: str = Query('',max_length=1000), offset: int = Query(0, ge=0)):
    require_protein(accession)
    if category not in ("normal", "cancer", "cell_line", "single_cell", "all"):
        raise HTTPException(422, "Unknown expression category")
    if context_key:
        spec=expression_spec(dataset)
        if spec[1]!='GTEx' and (not context_key.isdecimal() or int(context_key)>9223372036854775807):
            raise HTTPException(422,'Context key must be the original dataset context ID')
    context = ["expression", accession, source, category, dataset, context_key]
    state = cursor_read(cursor, context)
    jumping = state is None and offset > 0
    state = state or [0, offset]
    specs = ([GTEX_EXPRESSION] if category in ("normal","all") else []) + [s for s in EXPRESSION if category=="all" or s[2] == category]
    filters = {"sources": sorted({s[1] for s in specs}), "categories": ["normal", "cancer", "cell_line", "single_cell", "all"], "datasets": [{"value":s[0],"label":s[1]+" · "+s[3]+" · "+s[0].replace("_"," ")} for s in specs if not source or s[1]==source]}
    specs = [s for s in specs if (not source or s[1] == source) and (not dataset or s[0] == dataset)]
    index, offset = state
    items = []
    while index < len(specs) and len(items) <= limit:
        name, provider, actual_category, measurement, unit, extra = specs[index]
        params = {"accession": accession, "limit": limit + 1 - len(items), "offset": offset,
                  "context_key": context_key if provider=='GTEx' else int(context_key) if context_key else None}
        if provider == "GTEx":
            sql = ('''SELECT r.source_gene_id,s.sample_id context,s.sample_id context_key,r.values->>s.sample_index::int value,s.sample_index
                FROM web_context.expression_gtex_gene_median_tpm r
                JOIN web_context.expression_gtex_sample s ON s.dataset_id='gtex_expression:gtex_gene_median_tpm'
                WHERE r.hgnc_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)'''+
                (' AND s.sample_id=:context_key' if context_key else '')+'''
                ORDER BY r.source_gene_id,s.sample_index''')
        else:
            sql = (f'''SELECT r.* FROM web_context.expression_{name}_detail r
                WHERE r.hgnc_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)'''+
                (' AND r.context_id=:context_key' if context_key else '')+'''
                ORDER BY r.source_gene_id,r.context_id''')
        if jumping:
            count = one('SELECT count(*) records FROM (' + sql + ') selected', params)['records']
            if offset >= count:
                offset -= count
                index += 1
                continue
            jumping = False
        rows = query(sql + ' LIMIT :limit OFFSET :offset', params)
        for j, row in enumerate(rows):
            description = expression_context_label(row)
            items.append({"record_id": name + ":" + str(offset + j), "source": provider, "category": actual_category,
                          "context": description, "context_key":str(row.get('context_key') if provider=='GTEx' else row['context_id']),
                          "measurement": measurement, "value": clean(row.get("value") if provider == "GTEx" else row.get(measurement)),
                          "unit": unit, "details": fields(row, extra), "dataset": name,
                          "_cursor": [index, offset + j + 1]})
        if len(items) > limit:
            break
        index += 1
        offset = 0
    next_cursor = cursor_write(items[limit - 1]["_cursor"], context) if len(items) > limit else None
    for row in items:
        row.pop("_cursor", None)
    return {"items": items[:limit], "next_cursor": next_cursor, "filters": filters,
            "note": "Gene-level source measurements. Units and sample contexts are not pooled across studies."}
