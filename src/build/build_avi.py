"""Select the published AVI contribution and status tables for Web storage."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import shutil

import duckdb
import pyarrow.parquet as pq
import yaml

from Web.src.api.avi import FEATURES

WEB = Path(__file__).resolve().parents[2]
ROOT = WEB.parent


def main():
    cfg = yaml.safe_load((WEB / 'config/avi.yaml').read_text())
    source = ROOT / cfg['source_directory']
    source_manifest = json.loads((source / 'manifest.json').read_text())
    if source_manifest.get('state') != 'published':
        raise ValueError('AVI service input must be a published scientific snapshot.')
    scores = source / 'variant_avi_attribution.parquet'
    statuses = source / 'variant_avi_attribution_status.parquet'
    expected = pq.ParquetFile(scores).metadata.num_rows
    if pq.ParquetFile(statuses).metadata.num_rows != expected:
        raise ValueError('Published score and status row counts differ.')
    target = WEB / cfg['service_directory']
    stage = target.with_name(target.name + '.building')
    stage.mkdir(parents=True, exist_ok=False)
    try:
        with duckdb.connect(config={'threads': 4, 'memory_limit': '4GB'}) as connection:
            connection.read_parquet(str(scores)).create_view('scores')
            connection.read_parquet(str(statuses)).create_view('statuses')
            connection.execute('COPY (SELECT a.*,s.avi_attribution_status FROM scores a '
                               'JOIN statuses s USING(variant_id)) TO ? '
                               "(FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)",
                               [str(stage / 'attribution.parquet')])
        actual = pq.ParquetFile(stage / 'attribution.parquet').metadata.num_rows
        if actual != expected:
            raise ValueError('Service projection lost source records.')
        manifest = dict(data_version=source.name, schema=cfg['schema'],
                        built_at=datetime.now(timezone.utc).isoformat(),
                        source_directory=cfg['source_directory'], source_manifest=source_manifest,
                        tables=[dict(name='attribution', path='attribution.parquet', rows=actual,
                                     primary_key=['variant_id'])],
                        features=[dict(feature=f, column=f+'_contribution', label=l, group=g)
                                  for f, l, g in FEATURES])
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n')
        old = target.with_name(target.name + '.previous')
        if old.exists():
            raise FileExistsError('An earlier interrupted service replacement needs review.')
        if target.exists():
            target.rename(old)
        try:
            stage.rename(target)
        except BaseException:
            if old.exists():
                old.rename(target)
            raise
        if old.exists():
            shutil.rmtree(old)
        print(json.dumps(dict(status='built', rows=actual, output=str(target))))
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise


if __name__ == '__main__':
    main()
