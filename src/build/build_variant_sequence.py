"""Publish the confirmed representative-to-UniProt relation as small Web service tables."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq
import yaml

WEB = Path(__file__).resolve().parents[2]
ROOT = WEB.parent
SOURCE = ROOT / yaml.safe_load((WEB / 'config/variant.yaml').read_text())['inputs']['representative_sequence']
TARGET = WEB / 'data/tables/variant_sequence'
NAMES = ('representative_protein_sequence_status', 'representative_uniprot_sequence_relation')


def main():
    source_status = json.loads((SOURCE / 'status.json').read_text())
    if source_status['status'] != 'completed' or source_status['comparison_method'] != 'full_length_amino_acid_sequence_exact_equality':
        raise ValueError('Representative sequence source is not the confirmed exact-match release')
    tables = {name: pq.read_table(SOURCE / (name + '.parquet')) for name in NAMES}
    status = tables[NAMES[0]].to_pylist()
    relations = tables[NAMES[1]].to_pylist()
    if len(status) != source_status['representative_rows'] or len(relations) != source_status['relation_rows']:
        raise ValueError('Representative sequence source counts changed')
    genes = {row['gene_id'] for row in status}
    if len(genes) != len(status) or any(row['gene_id'] not in genes for row in relations):
        raise ValueError('Status identity or relation parent is invalid')
    keys = {(row['gene_id'], row['target_accession'], row['target_sequence_id']) for row in relations}
    if len(keys) != len(relations):
        raise ValueError('Duplicate target sequence relation')
    exact = sum(row['is_exact_match'] is True for row in relations)
    if exact != source_status['exact_match_relation_rows'] or exact != sum(row['exact_match_sequence_count'] for row in status):
        raise ValueError('Exact relation counts disagree with published status')

    temporary = TARGET.with_name('.variant_sequence_build_' + str(os.getpid()))
    temporary.mkdir(exist_ok=False)
    try:
        manifest = {'schema': 'web_variant_sequence', 'built_at': datetime.now(timezone.utc).isoformat(),
                    'input': str(SOURCE.relative_to(ROOT)), 'source_run_id': source_status['run_id'],
                    'comparison_method': source_status['comparison_method'], 'tables': []}
        for name in NAMES:
            path = temporary / (name + '.parquet')
            pq.write_table(tables[name], path, compression='zstd')
            rows = pq.ParquetFile(path).metadata.num_rows
            if rows != tables[name].num_rows:
                raise ValueError('Service Parquet count changed: ' + name)
            manifest['tables'].append({'name': name, 'path': 'variant_sequence/' + path.name,
                                       'rows': rows, 'primary_key': ['gene_id'] if name == NAMES[0] else []})
        (temporary / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        previous = TARGET.with_name('.variant_sequence_previous')
        if previous.exists():
            raise RuntimeError('Inspect interrupted prior publication before replacing service tables')
        if TARGET.exists():
            os.replace(TARGET, previous)
        try:
            os.replace(temporary, TARGET)
        except BaseException:
            if previous.exists():
                os.replace(previous, TARGET)
            raise
        if previous.exists():
            import shutil
            shutil.rmtree(previous)
        print(json.dumps({'status': 'built_validated', 'tables': {name: tables[name].num_rows for name in NAMES}, 'exact_matches': exact}))
    finally:
        if temporary.exists():
            import shutil
            shutil.rmtree(temporary)


if __name__ == '__main__':
    main()
