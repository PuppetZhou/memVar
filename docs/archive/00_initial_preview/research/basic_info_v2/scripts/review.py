"""Bounded Basic info review; writes research evidence, never service/DB tables."""
from __future__ import annotations
import json
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq

WEB = Path(__file__).resolve().parents[6]
DEST = Path(__file__).resolve().parents[1] / 'results'
sys.path.insert(0, str(WEB / 'src/build'))
from build_tables import Build, INPUTS, ROOT


def save(name, value):
    (DEST / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def audit_tables():
    manifest = json.loads((WEB / 'data/tables/manifest.json').read_text())
    tables = []
    for table in manifest['tables']:
        path = WEB / 'data/tables' / table['path']
        metadata = pq.ParquetFile(path).metadata
        sizes = Counter()
        for group_index in range(metadata.num_row_groups):
            group = metadata.row_group(group_index)
            for index in range(group.num_columns):
                column = group.column(index)
                sizes[column.path_in_schema.split('.')[0]] += column.total_compressed_size
        tables.append({k: table[k] for k in ['name', 'rows', 'primary_key', 'columns']} |
                      {'file_bytes': path.stat().st_size, 'compressed_column_bytes': dict(sizes)})
    save('table_inventory.json', {'checked_at': datetime.now(timezone.utc).isoformat(),
         'input_built_at': manifest['built_at'], 'tables': tables})


def validate_identity():
    with tempfile.TemporaryDirectory(prefix='memvar-basic-info-') as directory:
        build = Build(Path(directory))
        build.identity()
        refs = pl.read_parquet(build.tables['protein_external_reference'])
        old = pl.read_parquet(WEB / 'data/tables/identity/protein_external_reference.parquet')
        assert refs.height == old.height
        assert set(refs['reference_id']) == set(old['reference_id'])
        isoforms = pl.read_parquet(build.tables['protein_isoform']).select('accession', 'isoform_id')
        iso_refs = refs.filter(pl.col('scope_type') == 'isoform')
        assert iso_refs.join(isoforms, left_on=['accession', 'scope_id'],
                             right_on=['accession', 'isoform_id'], how='anti').height == 0
        refseq = refs.filter(pl.col('database_name') == 'RefSeq')
        assert refseq.filter(~pl.col('url').str.contains('/protein/')).height == 0
        assert refseq['transcript_id_full'].null_count() == 0
        assert refseq.filter(~pl.col('transcript_url').str.contains('/nuccore/')).height == 0
        for role in ['gene', 'protein', 'transcript']:
            assert refs.filter(pl.col(role + '_id_full').is_null() & pl.col(role + '_url').is_not_null()).height == 0
        save('link_validation.json', {'status': 'passed', 'output_status': 'temporary_validation_only',
             'source_rows_preserved': refs.height, 'refseq_protein_links_fixed': refseq.height,
             'refseq_source_transcript_pairs_retained': refseq.height,
             'ensembl_rows': refs.filter(pl.col('database_name') == 'Ensembl').height,
             'isoform_references_checked': iso_refs.height,
             'checks': ['stable_source_record_keys', 'missing_ID_has_no_URL',
                        'protein_vs_nucleotide_URL_types', 'isoform_declared_in_same_entry'],
             'examples': refs.filter((pl.col('accession') == 'P00533') &
                         pl.col('external_id').is_in(['NP_005219.2', 'ENST00000275493.7'])).to_dicts(),
             'limits': 'No full HTTP link crawl. Current service Parquet and PostgreSQL unchanged.'})


def membrane_preview():
    proteins = pl.read_parquet(WEB / 'data/tables/identity/protein.parquet')
    canonical = dict(proteins.select('accession', 'default_sequence_id').iter_rows())
    isoforms = pl.read_parquet(WEB / 'data/tables/identity/protein_isoform.parquet')
    canonical_isoforms = defaultdict(set)
    for row in isoforms.filter(pl.col('is_canonical')).iter_rows(named=True):
        canonical_isoforms[row['accession']].add(row['isoform_id'])
    support = defaultdict(lambda: defaultdict(list))
    features = pl.read_parquet(WEB / 'data/tables/membrane/membrane_uniprot_feature.parquet')
    for row in features.iter_rows(named=True):
        if row['mapped_sequence_id'] != canonical.get(row['accession']):
            continue
        label = None
        if row['source_type'] == 'Transmembrane':
            label = 'integral_membrane'
        elif row['source_type'] == 'Lipidation' and 'GPI-anchor' in (row['description'] or ''):
            label = 'lipid_anchored'
        if label:
            support[row['accession']][label].append(row['feature_id'])
    locations = pl.read_parquet(WEB / 'data/tables/localization/protein_uniprot_location.parquet')
    mapping = {'SL-9903': 'peripheral_membrane', 'SL-9901': 'lipid_anchored',
               'SL-9902': 'lipid_anchored', 'SL-9920': 'lipid_anchored'}
    for row in locations.iter_rows(named=True):
        eligible = row['scope_type'] == 'entry' or (row['scope_type'] == 'isoform' and
                    canonical_isoforms[row['accession']].intersection(row['isoform_ids']))
        if not eligible:
            continue
        for item in json.loads(row['locations_json']):
            label = mapping.get(item.get('topology', {}).get('id'))
            if label:
                support[row['accession']][label].append(row['annotation_id'])
    rows = []
    for accession in sorted(canonical):
        labels = support[accession]
        rows.append({'accession': accession, 'sequence_id': canonical[accession],
                     'labels': sorted(labels) or ['membrane_related'],
                     'support': {key: sorted(set(value)) for key, value in labels.items()}})
    counts = Counter(label for row in rows for label in row['labels'])
    save('membrane_rule_preview.json', {'status': 'proposal_preview_not_published',
         'scope': 'canonical features + entry-general/canonical UniProt topology; no cross-source inference',
         'protein_count': len(rows), 'counts': dict(counts),
         'overlap_proteins': sum(len(row['labels']) > 1 for row in rows),
         'examples': [row for row in rows if row['accession'] in ['P00533', 'O00165', 'P15328']]})
    pl.DataFrame([{'accession': row['accession'], 'sequence_id': row['sequence_id'],
                   'labels': ';'.join(row['labels']), 'support_json': json.dumps(row['support'])}
                  for row in rows]).write_csv(DEST / 'membrane_rule_preview.tsv', separator='\t')


def slim_preview():
    path = ROOT / INPUTS['go_slim']['path']
    slim = pl.read_csv(path, separator='\t').with_columns(
        (pl.lit('GO:') + pl.col('?x').str.extract(r'GO_(\d+)')).alias('go_id'))
    terms = pl.read_parquet(ROOT / INPUTS['go']['path'] / 'go_term.parquet')
    ids = set(slim['go_id'])
    assert slim.height == len(ids)
    known = terms.filter(pl.col('go_id').is_in(ids))
    assert known.height == len(ids)
    namespaces = dict(terms.select('go_id', 'namespace').iter_rows())
    edges = pl.read_parquet(ROOT / INPUTS['go']['path'] / 'go_term_relation.parquet')
    used = pl.read_parquet(WEB / 'data/tables/function_pathway/go_term.parquet')['go_id'].to_list()
    comparisons = {}
    for allowed in [('is_a',), ('is_a', 'part_of')]:
        parents = defaultdict(set)
        for child, relation, parent in edges.iter_rows():
            if relation in allowed:
                parents[child].add(parent)
        @lru_cache(None)
        def categories(term):
            result = {term} if term in ids else set()
            for parent in parents[term]:
                result.update(categories(parent))
            return frozenset(result)
        mapped = {term: {category for category in categories(term)
                         if namespaces.get(term) == namespaces.get(category)} for term in used}
        comparisons['+'.join(allowed)] = {'terms_with_category': sum(bool(v) for v in mapped.values()),
            'terms_without_category': sum(not v for v in mapped.values()),
            'term_category_pairs': sum(len(v) for v in mapped.values())}
    save('go_slim_preview.json', {'status': 'mapping_proposal_comparison_not_published',
         'subset_file': str(path.relative_to(ROOT)), 'category_count': len(ids),
         'namespaces': known.group_by('namespace').len().sort('namespace').to_dicts(),
         'service_term_count': len(used), 'comparisons': comparisons,
         'limits': 'Term-level graph reachability only; not protein function counts or new annotations.'})


def redundant_columns():
    tables = WEB / 'data/tables'
    rows = []
    for child, parent, key, columns in [
        ('identity/protein_function_overview', 'identity/protein', 'accession', ['default_sequence_id']),
        ('function_pathway/protein_rhea_reaction', 'function_pathway/rhea_reaction', 'rhea_id', ['master_id', 'direction']),
    ]:
        left = pl.read_parquet(tables / (child + '.parquet'), columns=[key, *columns])
        right = pl.read_parquet(tables / (parent + '.parquet'), columns=[key, *columns])
        joined = left.join(right, on=key, how='left', suffix='_parent', validate='m:1')
        assert left.height == joined.height
        for column in columns:
            rows.append({'table': child, 'column': column, 'via': parent + '.' + column,
                         'rows': left.height,
                         'different_rows': joined.filter(~pl.col(column).eq_missing(pl.col(column + '_parent'))).height})
    features = pl.read_parquet(tables / 'membrane/membrane_uniprot_feature.parquet')
    for left, right in [('source_sequence_id', 'mapped_sequence_id'), ('label', 'description'), ('feature_id', 'detail_id')]:
        rows.append({'table': 'membrane_uniprot_feature', 'column': left, 'via': right,
                     'rows': features.height, 'different_rows': features.filter(~pl.col(left).eq_missing(pl.col(right))).height})
    save('redundancy_checks.json', {'status': 'review_only_no_columns_dropped', 'comparisons': rows})


if __name__ == '__main__':
    if json.loads((WEB / 'data/tables/manifest.json').read_text()).get('data_version'):
        raise SystemExit('Historical pre-v2 review: current schema is normalized. Use Web/src/database/validate_import.py for current validation; preserve these earlier research results.')
    DEST.mkdir(parents=True, exist_ok=True)
    audit_tables()
    validate_identity()
    membrane_preview()
    slim_preview()
    redundant_columns()
