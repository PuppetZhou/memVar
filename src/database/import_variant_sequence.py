"""Atomically import the independent representative sequence service schema."""
import json
import os

from import_tables import TABLES, command, import_table, q, start


def main():
    manifest = json.loads((TABLES / 'variant_sequence/manifest.json').read_text())
    if manifest['comparison_method'] != 'full_length_amino_acid_sequence_exact_equality':
        raise ValueError('Only the published exact-sequence relation is supported')
    start()
    stage = 'web_variant_sequence_loading_' + str(os.getpid())
    command(f'CREATE SCHEMA {q(stage)}')
    try:
        for table in manifest['tables']:
            import_table(stage, table)
        status = q(stage) + '.representative_protein_sequence_status'
        relation = q(stage) + '.representative_uniprot_sequence_relation'
        command(f'CREATE INDEX ON {relation} (gene_id, is_exact_match)')
        command(f'CREATE INDEX ON {relation} (target_accession)')
        checks = {
            'orphan_relations': int(command(f'SELECT count(*) FROM {relation} r LEFT JOIN {status} s USING (gene_id) WHERE s.gene_id IS NULL', True)),
            'exact_matches': int(command(f'SELECT count(*) FROM {relation} WHERE is_exact_match = true', True)),
            'status_exact_matches': int(command(f'SELECT coalesce(sum(exact_match_sequence_count), 0) FROM {status}', True)),
        }
        if checks['orphan_relations'] or checks['exact_matches'] != checks['status_exact_matches']:
            raise ValueError('Imported representative sequence relation failed validation')
        command(f'ALTER TABLE {relation} ADD FOREIGN KEY (gene_id) REFERENCES {status} (gene_id)')
        target = manifest['schema']
        exists = command("SELECT count(*) FROM pg_namespace WHERE nspname='" + target + "'", True).strip() == '1'
        sql = 'BEGIN; SELECT pg_advisory_xact_lock(20260922, 6);'
        if exists:
            sql += f'ALTER SCHEMA {q(target)} RENAME TO {q(stage + "_old")};'
        sql += f'ALTER SCHEMA {q(stage)} RENAME TO {q(target)};'
        if exists:
            sql += f'DROP SCHEMA {q(stage + "_old")} CASCADE;'
        if command("SELECT count(*) FROM pg_roles WHERE rolname='memvar_api'", True).strip() == '1':
            sql += (f'GRANT USAGE ON SCHEMA {q(target)} TO memvar_api; '
                    f'GRANT SELECT ON ALL TABLES IN SCHEMA {q(target)} TO memvar_api; '
                    f'ALTER DEFAULT PRIVILEGES IN SCHEMA {q(target)} GRANT SELECT ON TABLES TO memvar_api;')
        command(sql + 'COMMIT;')
        print(json.dumps({'status': 'imported_validated', 'schema': target, 'checks': checks}))
    except BaseException:
        command(f'DROP SCHEMA IF EXISTS {q(stage)} CASCADE')
        raise


if __name__ == '__main__':
    main()
