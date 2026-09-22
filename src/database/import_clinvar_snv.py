"""Stage and atomically publish the independent ClinVar SNV service schema."""
import json
import os

from import_tables import TABLES, WEB, command, import_table, q, start

DATA = TABLES / 'clinvar_snv'


def main():
    manifest = json.loads((DATA / 'manifest.json').read_text())
    if manifest['status'] != 'built_from_validated_curated':
        raise ValueError('ClinVar service tables are not based on validated curated data')
    variant_manifest = json.loads((TABLES / 'variant/manifest.json').read_text())
    if manifest['current_variant_snapshot'] != variant_manifest['inputs']['variant']:
        raise ValueError('ClinVar and imported variant projections target different snapshots')
    start()
    stage = 'web_clinvar_snv_loading_' + str(os.getpid())
    schema = q(stage)
    command(f'CREATE SCHEMA {schema}')
    try:
        for table in manifest['tables']:
            import_table(stage, table)
        rcv = f'{schema}.rcv'
        scv = f'{schema}.scv'
        variant_rcv = f'{schema}.variant_rcv'
        variant_scv = f'{schema}.variant_scv'
        member = f'{schema}.rcv_condition_member'
        command(f'CREATE INDEX ON {variant_rcv} (source_row_id, variant_id); '
                f'CREATE INDEX ON {variant_scv} (source_row_id, variant_id); '
                f'CREATE INDEX ON {member} (rcv_id, rcv_version, variation_id); '
                f'CREATE INDEX ON {scv} (rcv_id, rcv_version, variation_id)')
        command(f'ALTER TABLE {variant_rcv} ADD FOREIGN KEY (rcv_id, rcv_version, variation_id) '
                f'REFERENCES {rcv} (rcv_id, rcv_version, variation_id); '
                f'ALTER TABLE {scv} ADD FOREIGN KEY (rcv_id, rcv_version, variation_id) '
                f'REFERENCES {rcv} (rcv_id, rcv_version, variation_id); '
                f'ALTER TABLE {member} ADD FOREIGN KEY (rcv_id, rcv_version, variation_id) '
                f'REFERENCES {rcv} (rcv_id, rcv_version, variation_id); '
                f'ALTER TABLE {variant_scv} ADD FOREIGN KEY '
                f'(variant_id, source_row_id, allele_id, variation_id, rcv_id, rcv_version) '
                f'REFERENCES {variant_rcv} '
                f'(variant_id, source_row_id, allele_id, variation_id, rcv_id, rcv_version); '
                f'ALTER TABLE {variant_scv} ADD FOREIGN KEY '
                f'(rcv_id, rcv_version, variation_id, scv_id, scv_version) '
                f'REFERENCES {scv} (rcv_id, rcv_version, variation_id, scv_id, scv_version)')
        orphan = int(command(f'''SELECT count(*) FROM {variant_rcv} v WHERE NOT EXISTS
            (SELECT 1 FROM web_variant.variant_source_link l WHERE l.variant_id=v.variant_id
             AND l.record_id=v.source_row_id)''', True))
        if orphan:
            raise ValueError(f'{orphan} ClinVar links lack a current Web variant source row')
        target = manifest['schema']
        exists = command("SELECT count(*) FROM pg_namespace WHERE nspname='" + target + "'", True).strip() == '1'
        sql = 'BEGIN; SELECT pg_advisory_xact_lock(20260922, 7);'
        if exists:
            sql += f'ALTER SCHEMA {q(target)} RENAME TO {q(stage + "_old")};'
        sql += f'ALTER SCHEMA {schema} RENAME TO {q(target)};'
        if exists:
            sql += f'DROP SCHEMA {q(stage + "_old")} CASCADE;'
        if command("SELECT count(*) FROM pg_roles WHERE rolname='memvar_api'", True).strip() == '1':
            sql += (f'GRANT USAGE ON SCHEMA {q(target)} TO memvar_api; '
                    f'GRANT SELECT ON ALL TABLES IN SCHEMA {q(target)} TO memvar_api; '
                    f'ALTER DEFAULT PRIVILEGES IN SCHEMA {q(target)} GRANT SELECT ON TABLES TO memvar_api;')
        command(sql + 'COMMIT;')
        report = {'status': 'imported_validated', 'schema': target, 'input': manifest['input'],
                  'source_xml_dated': manifest['source_xml_dated'], 'source_link_orphans': orphan,
                  'tables': {table['name']: table['rows'] for table in manifest['tables']}}
        (WEB / 'data/postgresql_clinvar_snv_import.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))
    except BaseException:
        command(f'DROP SCHEMA IF EXISTS {schema} CASCADE')
        raise


if __name__ == '__main__':
    main()
