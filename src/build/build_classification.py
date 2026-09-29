"""Publish the validated Q7 analysis snapshot as portable service tables."""
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.csv as csv
import pyarrow.parquet as pq
import yaml

WEB = Path(__file__).resolve().parents[2]
ROOT = WEB.parent


def main():
    config = yaml.safe_load((WEB / 'config/classification.yaml').read_text())
    source = yaml.safe_load((ROOT / config['source_config']).read_text())[config['source_key']]
    published = ROOT / source['published_directory']
    summary = json.loads((published / 'summary.json').read_text())
    validation = json.loads((published / 'validation.json').read_text())
    if summary['status'] != 'validated_analysis_mapping' or any(v is False for v in validation.values()):
        raise ValueError('Q7 mapping has not passed upstream validation')
    frozen = json.loads((published / 'config_snapshot.json').read_text())
    if any(source[k] != frozen[k] for k in ('rules_version', 'variant_mondo', 'published_directory')):
        raise ValueError('Published snapshot and source configuration differ')
    tables = WEB / 'data/tables'
    target = tables / 'classification'
    temp = tables / f'.classification_build_{os.getpid()}'
    temp.mkdir()
    try:
        inputs = {p.stem: p for p in sorted(published.glob('*.parquet'))}
        inputs['variant_mondo'] = ROOT / source['variant_mondo']
        keys = {'variant_mondo': ['variant_id', 'mondo_id'],
                'kegg_disease_entries': ['kegg_id'],
                'classification_categories': ['scheme', 'level', 'category_id']}
        for name, path in inputs.items():
            shutil.copyfile(path, temp / f'{name}.parquet')
        pq.write_table(csv.read_csv(published / 'classification_categories.csv'),
                       temp / 'classification_categories.parquet', compression='zstd')
        manifest = {**config, 'built_at': datetime.now(timezone.utc).isoformat(),
                    'status': 'built_from_validated_analysis', 'input': source['published_directory'],
                    'source_snapshot': frozen, 'summary': summary, 'upstream_validation': validation,
                    'tables': []}
        for path in sorted(temp.glob('*.parquet')):
            file = pq.ParquetFile(path)
            manifest['tables'].append({'name': path.stem, 'path': f'classification/{path.name}',
                'rows': file.metadata.num_rows, 'columns': file.schema_arrow.names,
                'primary_key': keys.get(path.stem, [])})
        (temp / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        previous = tables / '.classification_previous'
        if previous.exists():
            raise ValueError('Unresolved previous publication exists')
        if target.exists():
            target.rename(previous)
        try:
            temp.rename(target)
        except BaseException:
            if previous.exists():
                previous.rename(target)
            raise
        if previous.exists():
            shutil.rmtree(previous)
        print(json.dumps({t['name']: t['rows'] for t in manifest['tables']}))
    finally:
        if temp.exists():
            shutil.rmtree(temp)


if __name__ == '__main__':
    main()
