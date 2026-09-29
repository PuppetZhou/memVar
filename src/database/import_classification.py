"""Validate snapshot links and atomically replace the Q7 service schema."""
import json
import os
from import_tables import TABLES, WEB, command, import_table, q, start


def main():
    manifest = json.loads((TABLES / 'classification/manifest.json').read_text())
    if manifest['status'] != 'built_from_validated_analysis':
        raise ValueError('Expected validated Q7 service tables')
    start()
    stage = 'web_classification_loading_' + str(os.getpid())
    s = q(stage)
    command(f'CREATE SCHEMA {s}')
    try:
        for table in manifest['tables']:
            import_table(stage, table)
        command(f'''CREATE UNIQUE INDEX ON {s}.context_classification_mapping
            (subject_type,subject_namespace,subject_id,scheme,category_level,category_id) NULLS NOT DISTINCT;
            CREATE INDEX ON {s}.context_classification_mapping (subject_id,scheme,category_level)
            WHERE subject_type='disease' AND subject_namespace='MONDO';
            CREATE INDEX ON {s}.variant_mondo (mondo_id,variant_id);''')
        # Compare the imported bridge against the current DB source records in both
        # directions: a stale summary snapshot must never silently get these labels.
        dataset = manifest['clinvar_dataset_id'].replace("'", "''")
        checks = json.loads(command(f'''WITH direct AS MATERIALIZED (
            SELECT DISTINCT l.variant_id,'MONDO:' || right(trim(token),7) AS mondo_id
            FROM web_variant.variant_source_record r
            JOIN web_variant.variant_source_link l USING(record_id)
            CROSS JOIN LATERAL regexp_split_to_table(r.details_json->>'PhenotypeIDS','[,|;]') token
            WHERE r.dataset_id='{dataset}' AND trim(token) ~ '^MONDO:(MONDO:)?[0-9]{{7}}$'),
            missing AS (SELECT * FROM {s}.variant_mondo EXCEPT SELECT * FROM direct),
            extra AS (SELECT * FROM direct EXCEPT SELECT * FROM {s}.variant_mondo)
            SELECT json_build_object('bridge_not_in_current_summary',(SELECT count(*) FROM missing),
                'current_summary_not_in_bridge',(SELECT count(*) FROM extra),
                'unclassified_mondo_ids',(SELECT count(*) FROM {s}.variant_mondo b WHERE NOT EXISTS
                    (SELECT 1 FROM {s}.context_classification_mapping m WHERE m.subject_type='disease'
                     AND m.subject_namespace='MONDO' AND m.subject_id=b.mondo_id)));''', True))
        if any(checks.values()):
            raise ValueError(f'Snapshot relationship checks failed: {checks}')
        command(f'CREATE TABLE {s}._build_manifest (data_version text PRIMARY KEY,manifest jsonb NOT NULL)')
        literal = json.dumps(manifest, ensure_ascii=False).replace("'", "''")
        version = manifest['data_version'].replace("'", "''")
        command(f"INSERT INTO {s}._build_manifest VALUES ('{version}','{literal}'::jsonb)")
        target = manifest['schema']
        if target != 'web_classification':
            raise ValueError('Unexpected target schema')
        exists = command("SELECT count(*) FROM pg_namespace WHERE nspname='web_classification'", True).strip() == '1'
        sql = 'BEGIN; SELECT pg_advisory_xact_lock(20260929,7);'
        if exists:
            sql += f'ALTER SCHEMA {q(target)} RENAME TO {q(stage + "_old")};'
        sql += f'ALTER SCHEMA {s} RENAME TO {q(target)};'
        if exists:
            sql += f'DROP SCHEMA {q(stage + "_old")} CASCADE;'
        if command("SELECT count(*) FROM pg_roles WHERE rolname='memvar_api'", True).strip() == '1':
            sql += f'GRANT USAGE ON SCHEMA {q(target)} TO memvar_api; GRANT SELECT ON ALL TABLES IN SCHEMA {q(target)} TO memvar_api;'
        command(sql + 'COMMIT;')
        report = {'status': 'imported_validated', 'schema': target, 'built_at': manifest['built_at'],
                  'checks': checks, 'tables': {t['name']: t['rows'] for t in manifest['tables']}}
        (WEB / 'data/postgresql_classification_import.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))
    except BaseException:
        command(f'DROP SCHEMA IF EXISTS {s} CASCADE')
        raise


if __name__ == '__main__':
    main()
