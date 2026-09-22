"""Publish compact catalog statistics from validated reports and small live dimensions.

Run: python -m Web.src.database.build_catalog_statistics
Large table row counts are reused from the matching imported manifest/report.
No variant, QTL, expression or residue-level fact table is scanned.
"""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from Web.src.api.db import query, one
from Web.src.api.evidence import prediction_dictionary, prediction_group
from Web.src.api.core import MEMBRANE_CLASSES

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'Web/data'
MODULES = [
    ('proteins', 'Proteins and sequence annotations', 'web', 'postgresql_import.json'),
    ('variants', 'Variants and scores', 'web_variant', 'postgresql_variant_import.json'),
    ('context', 'Expression, QTL and interactions', 'web_context', 'postgresql_context_import.json'),
    ('diseases', 'Disease and phenotype evidence', 'web_disease', 'postgresql_disease_import.json'),
    ('interface', 'Interface predictions', 'web_interface', 'postgresql_interface_import.json'),
]


def read(path):
    return json.loads(path.read_text())


def metric(key, label, value, unit, basis='Validated import row count'):
    return dict(key=key, label=label, value=value, unit=unit, basis=basis)


def breakdown(key, title, unit, rows, note):
    return dict(key=key, title=title, unit=unit, rows=rows, note=note)


def build():
    manifests, reports, versions = {}, {}, []
    for key, label, schema, filename in MODULES:
        manifest = one(f'SELECT manifest FROM {schema}._build_manifest')['manifest']
        report = read(DATA / filename)
        if report['data_version'] != manifest['data_version'] or not report['status'].startswith('imported'):
            raise ValueError('Import report does not match the active database: ' + key)
        if isinstance(manifest['tables'], list):
            expected = {t['name']: t['rows'] for t in manifest['tables']}
            if report['tables'] != expected:
                raise ValueError('Imported row counts do not match the published manifest: ' + key)
        manifests[key], reports[key] = manifest, report
        versions.append(dict(module=key, label=label, service_version=manifest['data_version'],
                             built_at=manifest.get('built_at') or manifest.get('finished_at'),
                             upstream_versions=[]))
    base, variant, context, disease = (reports[k]['tables'] for k in ('proteins', 'variants', 'context', 'diseases'))
    protein_count = one('SELECT count(*) n FROM web.protein')['n']
    if protein_count != base['protein']:
        raise ValueError('Protein count differs from the validated import')

    class_counts = one('''SELECT
      count(*) FILTER (WHERE parent_class='integral_membrane') integral_membrane,
      count(*) FILTER (WHERE primary_class='transmembrane') transmembrane,
      count(*) FILTER (WHERE transmembrane_subclass='single_pass') single_pass,
      count(*) FILTER (WHERE transmembrane_subclass='multi_pass') multi_pass,
      count(*) FILTER (WHERE primary_class='lipid_anchored') lipid_anchored,
      count(*) FILTER (WHERE primary_class='peripheral_membrane') peripheral_membrane,
      count(*) FILTER (WHERE primary_class='membrane_related') membrane_related
      FROM web.protein_membrane_classification''')
    class_rows = [dict(label=label, value=class_counts[key], href='/search?membrane_class=' + key)
                  for key,label in MEMBRANE_CLASSES.items()]
    membrane_sources = query('''WITH associations AS (
        SELECT s.dataset_id source,c->>'accession' accession FROM web.membrane_topology_source s
            CROSS JOIN LATERAL jsonb_array_elements(s.protein_contexts) c
        UNION ALL SELECT dataset_id,accession FROM web.membrane_contact_identity)
        SELECT a.source label,count(DISTINCT p.accession) value FROM associations a
        JOIN web.protein p ON p.accession=a.accession GROUP BY a.source ORDER BY value DESC,a.source''')
    deep_count = one('''SELECT count(*) n FROM web.protein p JOIN web.deeptmhmm2_prediction d
        ON d.sequence_id=p.default_sequence_id WHERE d.status='ok' AND d.mapping_status='input_sequence_exact' ''')['n']
    membrane_sources = [dict(label='UniProt', value=protein_count), dict(label='DeepTMHMM2', value=deep_count)] + membrane_sources
    source_versions = query('SELECT source,version FROM web_variant.variant_dataset ORDER BY source')
    sources = read(ROOT / 'Web/config/catalog_sources.json')
    source_by_id = {r['id']: r for r in sources}
    release_by_id = {r['source'].lower(): r['version'] for r in source_versions
                     if r['version'] and not re.fullmatch(r'20\d{6}_.+', r['version'])}
    for row in query('SELECT DISTINCT source,source_release FROM web.sequence_dataset'):
        if row['source_release'] and re.fullmatch(r'[0-9][0-9_.-]*', row['source_release']):
            release_by_id[row['source'].lower()] = row['source_release']
    identity_inputs = manifests['proteins']['inputs']
    for name in ('go', 'reactome', 'rhea', 'gtopdb'):
        release_by_id[name] = str(identity_inputs[name]['version'])
    release_by_id['ensembl'] = next(r['version'] for r in source_versions if r['source']=='VEP')
    for row in query("SELECT DISTINCT provider,coalesce(details_json->>'version',details_json->>'source_release') version FROM web_context.context_dataset"):
        if row['provider'] in ('GTEx','HPA','BioGRID','eQTLGen','QTLbase') and row['version']:
            release_by_id[row['provider'].lower()] = row['version']
    disease_versions = query('SELECT source,source_version,reference_url FROM web_disease.disease_dataset ORDER BY source')
    release_by_id.update({r['source'].lower(): r['source_version'] for r in disease_versions if r['source_version']})
    for sid, release in release_by_id.items():
        if sid in source_by_id:
            source_by_id[sid]['version'] = release
            source_by_id[sid]['version_kind'] = 'VEP release' if sid=='ensembl' else 'Source release'
    release_modules = {
        'proteins': ('uniprot','go','reactome','rhea','gtopdb','pfam','glygen','ptmd2'),
        'variants': ('clinvar','cosmic','gnomad','dbnsfp','dbsnp','ensembl'),
        'context': ('gtex','hpa','biogrid','eqtlgen','qtlbase'),
        'diseases': ('clingen','gencc','hpo','omim','mondo','medgen'),
        'interface': (),
    }
    for version in versions:
        version['upstream_versions'] = [
            dict(name=source_by_id[sid]['name'], version=release_by_id[sid], kind=source_by_id[sid]['version_kind'])
            for sid in release_modules[version['module']] if sid in release_by_id]


    # This exact published input was retained in the active PostgreSQL build manifest.
    variant_input = ROOT / manifests['variants']['inputs']['variant'] / 'manifest.json'
    native = read(variant_input)
    if native['status'] != 'validated' or native['rounds']['hgvsp'] != {'rows': variant['variant_consequence'], 'variants': variant['variant']}:
        raise ValueError('Variant source statistics do not describe the active imported scope')
    if native['dbsnp_supplement']['links'] != variant['variant_dbsnp']:
        raise ValueError('dbSNP source statistics differ from imported rows')
    source_labels = {'gnomad': 'gnomAD', 'clinvar': 'ClinVar', 'cosmic': 'COSMIC', 'dbsnp': 'dbSNP'}
    source_rows = [dict(label=source_labels[k], value=v) for k,v in native['database_membership_variants'].items()]
    source_rows.sort(key=lambda r: -r['value'])
    prediction_dictionary.cache_clear()
    predictors = prediction_dictionary()
    tools = Counter(p['tool'] for p in predictors)
    groups = Counter(prediction_group(p['field']) for p in predictors)
    scopes = Counter(p['scope'] for p in predictors)
    if len(predictors) != variant['variant_prediction_field'] + 3:
        raise ValueError('Unexpected served predictor dictionary size')
    disease_sources = query('''SELECT d.source label,count(*) value FROM web_disease.gene_disease_evidence e
        JOIN web_disease.disease_dataset d USING(dataset_id) GROUP BY d.source ORDER BY value DESC,d.source''')
    if sum(r['value'] for r in disease_sources) != disease['gene_disease_evidence']:
        raise ValueError('Disease source counts differ from imported rows')
    disease_links = one('''SELECT count(DISTINCT accession) proteins,count(DISTINCT evidence_id) evidence,
        count(DISTINCT disease_id) diseases FROM web_disease.protein_disease_evidence''')
    expression_genes = one("""WITH genes AS (SELECT DISTINCT hgnc_id FROM web_context.expression_gene),
        project AS (SELECT DISTINCT hgnc_id FROM web.protein_gene)
        SELECT count(*) genes,count(*) FILTER(WHERE p.hgnc_id IS NULL) outside_project
        FROM genes g LEFT JOIN project p USING(hgnc_id)""")
    if expression_genes['outside_project']:
        raise ValueError('Expression gene dimension includes genes outside the current protein scope')


    sections = [dict(
        id='proteins', title='Membrane proteins',
        description='Reviewed human UniProt membrane-protein entries in the confirmed HGNC-linked project scope.',
        metrics=[metric('proteins','Protein entries',protein_count,'distinct UniProt accessions','Live protein dimension; matched to validated import'),
                 metric('sequences','Available sequences',base['protein_sequence'],'sequence IDs'),
                 metric('deeptmhmm2','DeepTMHMM2 coverage',deep_count,'canonical sequences with exact input match','Live protein and prediction dimensions')],
        breakdowns=[breakdown('classes','Primary membrane classification','proteins',class_rows,
                             'Every protein has one mutually exclusive primary branch. Integral and transmembrane are parent totals; their child counts must not be added to them.'),
                    breakdown('sources','Membrane annotation sources','associated proteins',membrane_sources,
                              'UniProt defines inclusion. Other sources annotate the existing protein set; association does not imply verified residue mapping. DeepTMHMM2 counts exact canonical-sequence predictions. Sources overlap.')],
        notes=['Inclusion: UniProt proteome UP000005640, reviewed:true, keyword KW-0472, followed by the confirmed HGNC-reference scope.',
               'Available sequences include canonical and non-canonical sequences; they are not additional protein entries.']),
        dict(id='variants', title='Genetic variants', description='Published GRCh38 single-nucleotide variants and their selected transcript consequences.',
        metrics=[metric('variants','Distinct variants',variant['variant'],'GRCh38 variant IDs'),
                 metric('consequences','Transcript annotations',variant['variant_consequence'],'variant–annotation–gene rows'),
                 metric('frequency','Variants with allele frequency',reports['variants']['checks']['frequency']['available'],'variants with a reported overall AF','Validated frequency import check')],
        breakdowns=[breakdown('sources','Database membership','distinct variants within each source',source_rows,
                              'One variant may belong to several sources. dbSNP is supplemental allele-matched membership; source counts must not be added to obtain unique variants.'),
                    breakdown('consequences','Reported consequences','annotation rows carrying each term',
                              [dict(label=k.replace('_',' '),value=v) for k,v in sorted(native['consequences'].items(),key=lambda item:-item[1])],
                              'A transcript annotation can contain several consequence terms. Counts overlap and do not represent clinical classifications.')],
        notes=['Variant uniqueness is defined by the published GRCh38 chromosome, position, reference and alternate allele identity.',
               'Transcript annotations are counted separately from genomic variants. An absent frequency is not a frequency of zero.']),
        dict(id='predictors', title='Variant prediction scores', description='Computational evidence available in the Variant Browser score selector.',
        metrics=[metric('tools','Named tools / model configurations',len(tools),'distinct tool labels','Live served predictor dictionary'),
                 metric('fields','Selectable score fields',len(predictors),'score fields','Live served predictor dictionary'),
                 metric('dbnsfp_fields','dbNSFP score fields',variant['variant_prediction_field'],'published dictionary fields'),
                 metric('alphagenome_fields','AlphaGenome score fields',sum(p['source']=='AlphaGenome' for p in predictors),'score fields','Live served predictor dictionary')],
        breakdowns=[breakdown('groups','Score categories','score fields',[dict(label=k,value=v) for k,v in groups.items()],
                              'Categories organize the existing selector and do not combine scores into a pathogenicity decision.'),
                    breakdown('tools','Tools and model configurations','score fields',[dict(label=k,value=v) for k,v in sorted(tools.items(),key=lambda item:item[0].lower())],
                              'Tool labels follow the published dictionary. Separately named configurations such as PolyPhen-2 HDIV and HVAR count separately; multiple fields are not independent evidence.'),
                    breakdown('scope','Score association level','score fields',[dict(label=k.replace('_',' '),value=v) for k,v in scopes.items()],
                              'Variant-level and transcript-consequence scores retain their original association level.')],
        notes=['Field availability does not imply a value is present for every variant. No global score-coverage percentage is inferred.',
               'ThermoMPNN ddG and protein-interface predictions are separate evidence modules and are not included in this selector count.']),
        dict(id='diseases', title='Disease evidence', description='Source-separated gene–disease assertions and phenotype annotations.',
        metrics=[metric('evidence','Gene–disease evidence records',disease['gene_disease_evidence'],'source evidence IDs'),
                 metric('diseases','Linked disease IDs',disease_links['diseases'],'source disease IDs linked to project proteins','Live small disease relations'),
                 metric('proteins','Proteins with disease evidence',disease_links['proteins'],'distinct protein accessions','Live small disease relations'),
                 metric('phenotypes','Phenotype annotations',disease['disease_phenotype'],'source phenotype annotation IDs')],
        breakdowns=[breakdown('sources','Gene–disease evidence sources','source evidence records',disease_sources,
                              'Source records have different grains, including assertions and navigation/activity records. Cross-source records may refer to the same relationship; counts are not independent clinical conclusions.')],
        notes=['Disease IDs from different vocabularies are retained separately. Gene-level disease evidence does not classify every variant in that gene.',
               'PTMD2 PTM–disease context records are displayed separately and are not added to gene–disease evidence counts.']),
        dict(id='context',title='Expression, regulation and interactions',description='Imported source records retain their study, unit and association context.',
        metrics=[metric('ppi','Stored interaction records',context['ppi_interaction'],'distinct stored interaction / mutation-feature record IDs'),
                 metric('qtl','QTL association records',sum(context[k] for k in ['gtex_qtl_pair','eqtlgen_cis','qtlbase_association']),'source association rows')],
        breakdowns=[breakdown('qtl','QTL association sources','source association rows',[
            dict(label='GTEx',value=context['gtex_qtl_pair']),dict(label='eQTLGen',value=context['eqtlgen_cis']),dict(label='QTLbase',value=context['qtlbase_association'])],
            'Source association records are not unique variants or independent discoveries. GTEx summary rows are excluded.'),
            breakdown('expression','Expression datasets shown in the browser','source observation rows',[
                dict(label=name.removeprefix('expression_').replace('_',' '),value=context[name]) for name in [
                    'expression_rna_tissue_hpa','expression_normal_ihc_data','expression_rna_tissue_fantom','expression_ms_tissue_sample_data',
                    'expression_cancer_data','expression_cancer_cptac','expression_rna_cancer_sample','expression_rna_celline',
                    'expression_rna_cell_line_cancer','expression_rna_single_cell_type','expression_rna_single_cell_cluster',
                    'expression_dvp_cell_type','expression_dvp_cell_type_group_data']],
                'These are source observation rows retained for confirmed project genes, not unique proteins, tissues or cells. Units are not pooled. GTEx median-expression vectors are excluded from this row comparison.')],
        notes=['Expression gene identities were checked against the current project protein–HGNC links; all imported expression genes belong to that scope.',
               'PPI collection memberships overlap; interaction and mutation-feature records retain separate meanings.',
               'Expression rows with missing measurements remain part of the imported source data.'])]
    return dict(schema_version=1, generated_at=datetime.now(timezone.utc).isoformat(), versions=versions, sources=sources, sections=sections,
                notes=['Counts describe the active published service snapshots shown below, not upstream databases in their entirety.',
                       'Large-table totals reuse validated import reports matched to active PostgreSQL manifests; small dimensions are checked during generation.',
                       'Source-release versions and published processing snapshots are distinct. Unknown source releases remain unspecified.'])


def main():
    result = build()
    path = DATA / 'catalog_statistics.json'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)
    print('Published catalog_statistics.json:', {s['id']: len(s['metrics']) for s in result['sections']})


if __name__ == '__main__':
    main()
