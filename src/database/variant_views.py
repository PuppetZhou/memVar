"""Query projections share stored identities, consequences, evidence and substitutions."""
from import_tables import q

def statements(schema):
 s=q(schema)
 yield 'variant_source_detail',f'''CREATE OR REPLACE VIEW {s}.variant_source_detail AS
SELECT l.variant_id,l.alt_index,r.record_id,d.source,d.version,r.native_id,r.details_json
FROM {s}.variant_source_link l JOIN {s}.variant_source_record r USING(record_id)
JOIN {s}.variant_dataset d USING(dataset_id);'''
 yield 'variant_database',f'''CREATE OR REPLACE VIEW {s}.variant_database AS
SELECT DISTINCT l.variant_id,d.source AS database_name FROM {s}.variant_source_link l
JOIN {s}.variant_source_record r USING(record_id) JOIN {s}.variant_dataset d USING(dataset_id)
WHERE d.source IN ('ClinVar','COSMIC','gnomAD')
UNION SELECT variant_id,'dbSNP' FROM {s}.variant_dbsnp;'''
 yield 'variant_rsid',f'''CREATE OR REPLACE VIEW {s}.variant_rsid AS
SELECT DISTINCT variant_id,rsid FROM {s}.variant_dbsnp;'''
 yield 'canonical_ddg_site',f'''CREATE OR REPLACE VIEW {s}.canonical_ddg_site AS
SELECT d.* FROM {s}.ddg_prediction d JOIN web.protein p ON p.accession=d.accession AND p.default_sequence_id=d.sequence_id;'''
 yield 'variant_ddg_detail',f'''CREATE OR REPLACE VIEW {s}.variant_ddg_detail AS
SELECT l.annotation_id,l.variant_id,l.gene_id,d.* FROM {s}.variant_ddg_link l
JOIN {s}.canonical_ddg_site d USING(prediction_id);'''
 yield 'protein_variant',f'''CREATE OR REPLACE VIEW {s}.protein_variant AS
SELECT g.accession,c.* FROM web.protein_gene g JOIN {s}.variant_consequence c ON c.gene_id=g.hgnc_id;'''
