"""Record exact pre-migration equivalence checks for the selected redundant data."""
import json
from datetime import datetime, timezone
from pathlib import Path
import polars as pl
import yaml

WEB = Path(__file__).resolve().parents[2]


def main():
    manifest = json.loads((WEB / 'data/tables/manifest.json').read_text())
    rules = yaml.safe_load((WEB / 'config/tables.yaml').read_text())
    output = WEB / 'docs/record' / (rules['data_version'] + '_audit.json')
    if output.exists():
        raise FileExistsError('Baseline already recorded; do not replace it after migration')
    tables = WEB / 'data/tables'
    p = pl.read_parquet(tables / 'identity/protein.parquet')
    f = pl.read_parquet(tables / 'identity/protein_function_overview.parquet')
    joined = f.join(p.select('accession','default_sequence_id'),on='accession',suffix='_protein',validate='1:1')
    assert joined.height == f.height
    assert joined.filter(~pl.col('default_sequence_id').eq_missing(pl.col('default_sequence_id_protein'))).is_empty()
    assert f['selection_rule'].unique().to_list() == [rules['metadata']['function_selection_rule']]
    assert p['inclusion_basis'].unique().to_list() == [rules['metadata']['protein_inclusion_basis']]
    assert pl.read_parquet(tables/'localization/protein_uniprot_location.parquet')['comment_type'].unique().to_list() == ['SUBCELLULAR LOCATION']
    a = pl.read_parquet(tables/'function_pathway/protein_rhea_reaction.parquet')
    r = pl.read_parquet(tables/'function_pathway/rhea_reaction.parquet')
    joined = a.join(r.select('rhea_id','master_id','direction'),on='rhea_id',suffix='_reaction',validate='m:1')
    assert joined.height == a.height
    for c in ['master_id','direction']:
        assert joined.filter(~pl.col(c).eq_missing(pl.col(c+'_reaction'))).is_empty()
    b = pl.read_parquet(tables/'membrane/membrane_biodolphin_interaction.parquet')
    sites = pl.read_parquet(tables/'membrane/membrane_biodolphin_site.parquet')
    nested = b.select('interaction_id','source_sites').explode('source_sites').filter(pl.col('source_sites').is_not_null()).unnest('source_sites')
    keys = ['interaction_id','coordinate_system','site_order']
    assert nested.sort(keys).equals(sites.select(nested.columns).sort(keys),null_equal=True)
    counts = sites.group_by('interaction_id').agg(pl.len().alias('total'),(pl.col('mapping_status')=='mapped').sum().alias('mapped'))
    summary=b.join(counts,on='interaction_id',how='left')
    assert summary.filter(~pl.col('source_site_rows').eq_missing(pl.col('total')) | ~pl.col('mapped_site_rows').eq_missing(pl.col('mapped'))).is_empty()
    refs = pl.read_parquet(tables/'identity/protein_external_reference.parquet')
    genes = pl.read_parquet(tables/'identity/protein_gene.parquet')
    assert set(refs.filter(pl.col('database_name')=='UniProt').select('accession','external_id').iter_rows()) == {(x,x) for x in p['accession']}
    assert set(refs.filter(pl.col('database_name')=='HGNC').select('accession','external_id').iter_rows()) == set(genes.select('accession','hgnc_id').iter_rows())
    previous_import = json.loads((WEB/'data/postgresql_import.json').read_text())
    report = dict(status='passed',checked_at=datetime.now(timezone.utc).isoformat(),
                  previous_built_at=manifest['built_at'],new_data_version=rules['data_version'],
                  previous_database_bytes=previous_import['database_size_bytes'],
                  previous_table_rows={t['name']:t['rows'] for t in manifest['tables']},
                  previous_columns={t['name']:list(t['columns']) for t in manifest['tables']},
                  checks={'overview_sequence_equal_rows':f.height,'rhea_equal_rows':a.height,
                          'biodolphin_equal_site_records':nested.height,
                          'biodolphin_equal_summary_rows':summary.height,
                          'uniprot_duplicate_rows':p.height,'hgnc_duplicate_rows':genes.height,
                          'complete_external_reference_rows':refs.height,
                          'constant_columns':['protein.inclusion_basis','protein_function_overview.selection_rule','protein_uniprot_location.comment_type']})
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report['checks'],ensure_ascii=False))


if __name__ == '__main__':
    main()
