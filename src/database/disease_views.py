"""Ordinary disease views reconstruct reused fields and existing protein links."""
from import_tables import q

def statements(schema):
 s=q(schema)
 yield 'gene_protein_link',f'''CREATE VIEW {s}.gene_protein_link AS
SELECT gene_id,accession FROM {s}.gene_protein_ncbi
UNION ALL SELECT p.hgnc_id AS gene_id,p.accession FROM web.protein_gene p
JOIN (SELECT gene_id FROM {s}.gene_disease_evidence UNION SELECT gene_id FROM {s}.gene_dosage) g ON g.gene_id=p.hgnc_id;'''
 yield 'disease_entry_detail',f'''CREATE VIEW {s}.disease_entry_detail AS
SELECT e.*,d.definition,d.definition_source FROM {s}.disease_entry e
LEFT JOIN {s}.disease_definition d ON d.definition_id=e.primary_definition_id;'''
 yield 'disease_description',f'''CREATE VIEW {s}.disease_description AS
SELECT l.disease_id,d.definition,d.definition_source,l.source_record,l.via,l.display_eligible,s.source_version
FROM {s}.disease_definition_link l JOIN {s}.disease_definition d USING(definition_id)
JOIN {s}.disease_dataset s USING(dataset_id);'''
 yield 'disease_source_label',f'''CREATE VIEW {s}.disease_source_label AS
SELECT d.disease_id,d.label,d.source,o.source_record FROM {s}.disease_label_origin o JOIN {s}.disease_label d USING(label_id);'''
 yield 'gene_disease_evidence_detail',f'''CREATE VIEW {s}.gene_disease_evidence_detail AS
SELECT e.*,d.source,d.source_version FROM {s}.gene_disease_evidence e JOIN {s}.disease_dataset d USING(dataset_id);'''
 yield 'gene_dosage_detail',f'''CREATE VIEW {s}.gene_dosage_detail AS
SELECT e.*,d.source_version FROM {s}.gene_dosage e JOIN {s}.disease_dataset d USING(dataset_id);'''
 yield 'disease_phenotype_detail',f'''CREATE VIEW {s}.disease_phenotype_detail AS
SELECT p.*,p.disease_id AS database_id,l.label AS disease_name,t.name AS hpo_name,d.source_version
FROM {s}.disease_phenotype p LEFT JOIN {s}.ontology_term t ON t.term_id=p.resolved_hpo_id
LEFT JOIN {s}.disease_label_origin o USING(label_occurrence_id)
LEFT JOIN {s}.disease_label l USING(label_id) JOIN {s}.disease_dataset d ON d.dataset_id=p.dataset_id;'''
 yield 'protein_disease_evidence',f'''CREATE VIEW {s}.protein_disease_evidence AS
SELECT g.accession,e.* FROM {s}.gene_protein_link g JOIN {s}.gene_disease_evidence_detail e USING(gene_id);'''
 yield 'medgen_names',f'''CREATE VIEW {s}.medgen_names AS
SELECT x->>'CUI' AS "CUI",x->>'name' AS name,x->>'source' AS source,x->>'SUPPRESS' AS "SUPPRESS",c.resolved_cui,(x->>'display_eligible')::boolean AS display_eligible
FROM {s}.medgen_concept c CROSS JOIN LATERAL jsonb_array_elements(c.names) x;'''
 yield 'medgen_definitions',f'''CREATE VIEW {s}.medgen_definitions AS
SELECT x->>'CUI' AS "CUI",d.definition AS "DEF",x->>'source' AS source,x->>'SUPPRESS' AS "SUPPRESS",c.resolved_cui,(x->>'display_eligible')::boolean AS display_eligible
FROM {s}.medgen_concept c CROSS JOIN LATERAL jsonb_array_elements(c.definitions) x
JOIN {s}.disease_definition d ON d.definition_id=x->>'definition_id';'''
 yield 'disease_mondo_link_detail',f'''CREATE VIEW {s}.disease_mondo_link_detail AS
SELECT l.*,e.mondo_mapping_status AS mapping_status FROM {s}.disease_mondo_link l JOIN {s}.disease_entry e USING(disease_id);'''
 yield 'disease_medgen_link_detail',f'''CREATE VIEW {s}.disease_medgen_link_detail AS
SELECT l.*,false AS identity_merge_allowed FROM {s}.disease_medgen_link l;'''
