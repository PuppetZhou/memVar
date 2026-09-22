"""Copy the validated five-table ClinVar SNV relation into Web service Parquet.

This entrypoint refuses run-local or unvalidated data. It does no condition
matching or classification; those decisions belong to the disease module.
"""
import json
import os
from pathlib import Path
import shutil
from datetime import datetime, timezone

import pyarrow.parquet as pq
import yaml

WEB = Path(__file__).resolve().parents[2]
ROOT = WEB.parent
CFG = yaml.safe_load((WEB / 'config/clinvar_snv.yaml').read_text())
SOURCE = ROOT / CFG['input']
TARGET = WEB / 'data/tables/clinvar_snv'
KEYS = {
    'variant_rcv': ['variant_id', 'source_row_id', 'allele_id', 'variation_id', 'rcv_id', 'rcv_version'],
    'rcv': ['rcv_id', 'rcv_version', 'variation_id'],
    'scv': ['rcv_id', 'rcv_version', 'variation_id', 'scv_id', 'scv_version'],
    'variant_scv': ['variant_id', 'source_row_id', 'allele_id', 'variation_id', 'rcv_id', 'rcv_version', 'scv_id', 'scv_version'],
    'rcv_condition_member': ['rcv_id', 'rcv_version', 'variation_id', 'member_index'],
}
REQUIRED = {
    'variant_rcv': {'variant_id', 'source_row_id', 'allele_id', 'variation_id', 'rcv_id', 'rcv_version', 'source_dated', 'version_basis'},
    'rcv': {'rcv_id', 'rcv_version', 'variation_id', 'trait_set_id', 'trait_set_type', 'germline_classification', 'germline_review_status', 'somatic_clinical_impact', 'somatic_review_status', 'oncogenicity_classification', 'oncogenicity_review_status', 'source_dated'},
    'scv': {'rcv_id', 'rcv_version', 'variation_id', 'scv_id', 'scv_version', 'submitter', 'org_id', 'germline_classification', 'somatic_clinical_impact', 'oncogenicity_classification', 'review_status', 'date_last_evaluated', 'source_dated'},
    'variant_scv': {'variant_id', 'source_row_id', 'allele_id', 'variation_id', 'rcv_id', 'rcv_version', 'scv_id', 'scv_version', 'summary_referenced_by_id', 'summary_fields', 'summary_version_status'},
    'rcv_condition_member': {'rcv_id', 'rcv_version', 'variation_id', 'member_index', 'trait_id', 'trait_type', 'names_json', 'xrefs_json'},
}


def main():
    report = json.loads((SOURCE / 'report.json').read_text())
    if report.get('status') != 'published' or report.get('source_xml_dated') != '2026-09-05':
        raise ValueError('ClinVar SNV evidence has not been formally published and validated')
    if report.get('current_variant_snapshot') != CFG['current_variant_snapshot']:
        raise ValueError('ClinVar relation targets a different variant snapshot')
    temporary = TARGET.with_name('.clinvar_snv_build_' + str(os.getpid()))
    temporary.mkdir(exist_ok=False)
    try:
        tables = []
        for name, keys in KEYS.items():
            source = SOURCE / (name + '.parquet')
            metadata = pq.ParquetFile(source)
            if not REQUIRED[name].issubset(metadata.schema_arrow.names):
                raise ValueError('ClinVar formal table schema differs: ' + name)
            expected = report['table_rows'][name]
            if metadata.metadata.num_rows != expected:
                raise ValueError('ClinVar formal table count differs: ' + name)
            destination = temporary / source.name
            shutil.copy2(source, destination)
            tables.append({'name': name, 'path': 'clinvar_snv/' + source.name, 'rows': expected,
                           'primary_key': keys, 'columns': {field.name: str(field.type) for field in metadata.schema_arrow}})
        manifest = {'data_version': CFG['data_version'], 'schema': CFG['schema'],
                    'built_at': datetime.now(timezone.utc).isoformat(), 'input': CFG['input'],
                    'current_variant_snapshot': CFG['current_variant_snapshot'],
                    'source_xml_dated': report['source_xml_dated'], 'tables': tables,
                    'status': 'built_from_validated_curated'}
        (temporary / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        previous = TARGET.with_name('.clinvar_snv_previous')
        if previous.exists():
            raise RuntimeError('Inspect interrupted prior ClinVar service publication')
        if TARGET.exists():
            os.replace(TARGET, previous)
        try:
            os.replace(temporary, TARGET)
        except BaseException:
            if previous.exists():
                os.replace(previous, TARGET)
            raise
        if previous.exists():
            shutil.rmtree(previous)
        print(json.dumps({'status': manifest['status'], 'tables': {t['name']: t['rows'] for t in tables}}))
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


if __name__ == '__main__':
    main()
