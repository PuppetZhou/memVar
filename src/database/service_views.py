"""Non-materialized service views: expose complete relations without storing copies."""


def q(value):
    return '"' + value.replace('"', '""') + '"'


def literal(value):
    return "'" + value.replace("'", "''") + "'"


def statements(schema, manifest):
    s = q(schema)
    rule = literal(manifest['rules']['metadata']['function_selection_rule'])
    hgnc_release = literal(str(manifest['inputs']['protein_gene']['version']))
    yield 'protein_external_reference_all', f'''
CREATE VIEW {s}.protein_external_reference_all AS
WITH refs AS (
 SELECT reference_id,accession,database_name,scope_type,scope_id,external_id,identifier_type,url,
        gene_id_full,protein_id_full,nucleotide_id_full,source_record_key,source_release
 FROM {s}.protein_external_reference
 UNION ALL
 SELECT 'uniprot:'||accession,accession,'UniProt','entry',accession,accession,'protein_entry',
        'https://www.uniprot.org/uniprotkb/'||accession||'/entry',NULL,NULL,NULL,accession,source_release
 FROM {s}.protein
 UNION ALL
 SELECT 'hgnc:'||accession||':'||hgnc_id,accession,'HGNC','gene',hgnc_id,hgnc_id,'gene',
        'https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/'||hgnc_id,
        NULL,NULL,NULL,hgnc_id,{hgnc_release}
 FROM {s}.protein_gene
), typed AS (
 SELECT reference_id,accession,database_name,scope_type,scope_id,external_id,identifier_type,url,
        coalesce(gene_id_full,CASE WHEN identifier_type='gene' THEN external_id END) AS gene_id_full,
        coalesce(protein_id_full,CASE WHEN identifier_type='protein' THEN external_id END) AS protein_id_full,
        CASE WHEN identifier_type='transcript' THEN external_id
             WHEN database_name='RefSeq' AND nucleotide_id_full ~ '^(NM|XM|NR|XR)_[0-9]+([.][0-9]+)?$'
             THEN nucleotide_id_full END AS transcript_id_full,
        coalesce(nucleotide_id_full,CASE WHEN database_name='RefSeq' AND identifier_type IN ('nucleotide','transcript')
                                        THEN external_id END) AS nucleotide_id_full,
        source_record_key,source_release
 FROM refs
)
SELECT *,
 CASE WHEN database_name='Ensembl' AND gene_id_full ~ '^ENSG[0-9]+(\\.[0-9]+)?$'
      THEN 'https://www.ensembl.org/id/'||gene_id_full
      WHEN database_name='HGNC' AND gene_id_full ~ '^HGNC:[0-9]+$'
      THEN 'https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/'||gene_id_full END AS gene_url,
 CASE WHEN database_name='Ensembl' AND protein_id_full ~ '^ENSP[0-9]+(\\.[0-9]+)?$'
      THEN 'https://www.ensembl.org/id/'||protein_id_full
      WHEN database_name='RefSeq' AND protein_id_full ~ '^(NP|XP|YP|WP|AP|ZP)_[0-9]+(\\.[0-9]+)?$'
      THEN 'https://www.ncbi.nlm.nih.gov/protein/'||protein_id_full END AS protein_url,
 CASE WHEN database_name='Ensembl' AND transcript_id_full ~ '^ENST[0-9]+(\\.[0-9]+)?$'
      THEN 'https://www.ensembl.org/id/'||transcript_id_full
      WHEN database_name='RefSeq' AND transcript_id_full ~ '^(NM|XM|NR|XR)_[0-9]+(\\.[0-9]+)?$'
      THEN 'https://www.ncbi.nlm.nih.gov/nuccore/'||transcript_id_full END AS transcript_url,
 CASE WHEN database_name='RefSeq' AND nucleotide_id_full ~ '^(NM|XM|NR|XR|NC|NG|NT|NW|NZ)_[A-Za-z0-9]+([.][0-9]+)?$'
      THEN 'https://www.ncbi.nlm.nih.gov/nuccore/'||nucleotide_id_full END AS nucleotide_url
FROM typed;'''
    yield 'protein_function_overview_detail', f'''
CREATE VIEW {s}.protein_function_overview_detail AS
SELECT o.*,p.default_sequence_id,{rule}::text AS selection_rule
FROM {s}.protein_function_overview o JOIN {s}.protein p USING(accession);'''
    yield 'protein_rhea_reaction_detail', f'''
CREATE VIEW {s}.protein_rhea_reaction_detail AS
SELECT a.*,r.master_id,r.direction
FROM {s}.protein_rhea_reaction a JOIN {s}.rhea_reaction r USING(rhea_id);'''
    yield 'membrane_biodolphin_interaction_summary', f'''
CREATE VIEW {s}.membrane_biodolphin_interaction_summary AS
SELECT b.*,nullif(n.total,0) AS source_site_rows,
 CASE WHEN n.total>0 THEN n.mapped END AS mapped_site_rows,
 CASE WHEN n.total=0 THEN 'source_sites_absent'
      WHEN n.mapped=n.total THEN 'all_source_sites_mapped'
      WHEN n.mapped>0 THEN 'partially_mapped' ELSE 'no_verified_mapping' END AS sequence_mapping_status
FROM {s}.membrane_biodolphin_interaction b
CROSS JOIN LATERAL (
 SELECT count(*) AS total,count(*) FILTER (WHERE mapping_status='mapped') AS mapped
 FROM {s}.membrane_biodolphin_site x WHERE x.interaction_id=b.interaction_id
) n;'''
    yield 'protein_go_slim', f'''
CREATE VIEW {s}.protein_go_slim AS
SELECT a.accession,a.annotation_id,a.subject_id,a.form_id,a.go_id,m.category_id,
       a.relation,a.extension,a.evidence_code,a.reference,a.mapping_status
FROM {s}.protein_go_annotation a
JOIN {s}.go_slim_mapping m ON m.term_id=a.go_id
JOIN {s}.go_term t ON t.go_id=a.go_id
WHERE a.mapping_status IN ('exact_entry','declared_isoform')
  AND a.term_status='resolved' AND NOT a.is_negative AND a.evidence_code<>'ND'
  AND NOT t.is_obsolete AND a.go_id NOT IN ('GO:0003674','GO:0008150','GO:0005575');'''
    if any(t['name']=='uniprot_sequence_feature' for t in manifest['tables']):
        types=','.join(literal(x) for x in manifest['rules']['uniprot_membrane_types'])
        yield 'membrane_uniprot_feature',f'''CREATE VIEW {s}.membrane_uniprot_feature AS
SELECT * FROM {s}.uniprot_sequence_feature WHERE source_type IN ({types});'''
        yield 'sequence_uniprot_feature',f'''CREATE VIEW {s}.sequence_uniprot_feature AS
SELECT f.*,f.mapped_sequence_id AS sequence_id FROM {s}.uniprot_sequence_feature f
JOIN {s}.protein p ON p.accession=f.accession AND p.default_sequence_id=f.mapped_sequence_id;'''
        table=next(t for t in manifest['tables'] if t['name']=='ptm_record')
        fallback={'source_start':'start','source_end':'end','source_type':'source_type','source_sequence_id':'source_sequence_id','source_object_id':'feature_id','description':'description','details_json':'details_json'}
        cols=','.join(f'coalesce(r.{q(c)},f.{q(fallback[c])}) AS {q(c)}' if c in fallback else f'r.{q(c)}' for c in table['columns'])
        yield 'ptm_record_detail',f'''CREATE VIEW {s}.ptm_record_detail AS
SELECT {cols},
CASE WHEN r.mapping_status IN ('full_sequence_exact','full_sequence_equal_identifier_changed','original_window_exact','uniprot_native_exact') THEN p.default_sequence_id END AS mapped_sequence_id,
CASE WHEN r.mapping_status IN ('full_sequence_exact','full_sequence_equal_identifier_changed','original_window_exact','uniprot_native_exact') THEN coalesce(r.source_start,f.start) END AS mapped_start,
CASE WHEN r.mapping_status IN ('full_sequence_exact','full_sequence_equal_identifier_changed','original_window_exact','uniprot_native_exact') THEN coalesce(r.source_end,f."end") END AS mapped_end
FROM {s}.ptm_record r LEFT JOIN {s}.uniprot_sequence_feature f ON f.feature_id=r.uniprot_feature_id
LEFT JOIN {s}.protein p ON p.accession=r.accession;'''
        yield 'ptm_evidence_all',f'''CREATE VIEW {s}.ptm_evidence_all AS
SELECT e.evidence_id,e.record_id,e.namespace,e.identifier,coalesce(e.url,d.url) AS url,
 e.evidence_kind,coalesce(e.is_current,d.is_current) AS is_current,e.field_path,
 coalesce(e.payload_json,d.details_json) AS details_json
FROM {s}.ptm_evidence e LEFT JOIN {s}.ptm_evidence_dataset d
 ON e.namespace='ProteomeScout_dataset' AND e.identifier=d.source_dataset_id
UNION ALL
SELECT r.record_id||':feature-evidence:'||(x->>'evidence_id'),r.record_id,
 x->>'source',x->>'source_id',
 CASE WHEN x->>'source'='PubMed' AND x->>'source_id' ~ '^[0-9]+$'
 THEN 'https://pubmed.ncbi.nlm.nih.gov/'||(x->>'source_id')||'/' END,
 x->>'evidence_code',NULL::boolean,x->>'field_path',NULL::jsonb
FROM {s}.ptm_record r JOIN {s}.uniprot_sequence_feature f ON f.feature_id=r.uniprot_feature_id
CROSS JOIN LATERAL jsonb_array_elements(f.evidences) x;'''
        yield 'sequence_ptm_site',f'''CREATE VIEW {s}.sequence_ptm_site AS
SELECT s.sequence_id,s.position,s.residue,l.record_id,l.endpoint_role,l.mapping_method,
 r.dataset_id,r.topic,r.source_type,r.description,r.evidence_status
FROM {s}.sequence_site s JOIN {s}.ptm_record_site l USING(site_id)
JOIN {s}.ptm_record_detail r USING(record_id);'''
