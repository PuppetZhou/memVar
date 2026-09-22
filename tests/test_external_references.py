import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/build'))
from external_references import identifier_url, reference_fields, uniprot_xref_fields


class ExternalReferencesTest(unittest.TestCase):
    def test_refseq_source_pair_has_distinct_endpoints(self):
        fields = uniprot_xref_fields({
            'database': 'RefSeq', 'external_id': 'NP_005219.2',
            'properties_json': '[{"key":"NucleotideSequenceId","value":"NM_005228.5"}]',
        })
        self.assertEqual(fields['protein_id_full'], 'NP_005219.2')
        self.assertEqual(fields['transcript_id_full'], 'NM_005228.5')
        self.assertEqual(fields['url'], 'https://www.ncbi.nlm.nih.gov/protein/NP_005219.2')
        self.assertEqual(fields['transcript_url'], 'https://www.ncbi.nlm.nih.gov/nuccore/NM_005228.5')
        self.assertIsNone(fields['gene_id_full'])

    def test_ensembl_preserves_three_source_identifiers_and_versions(self):
        fields = uniprot_xref_fields({
            'database': 'Ensembl', 'external_id': 'ENST00000275493.7',
            'gene_id_full': 'ENSG00000146648.22', 'protein_id_full': 'ENSP00000275493.2',
        })
        self.assertEqual(fields['identifier_type'], 'transcript')
        self.assertEqual(fields['transcript_id_full'], 'ENST00000275493.7')
        self.assertEqual(fields['gene_url'], 'https://www.ensembl.org/id/ENSG00000146648.22')
        self.assertEqual(fields['protein_url'], 'https://www.ensembl.org/id/ENSP00000275493.2')

    def test_missing_and_unrecognized_ids_do_not_create_links(self):
        for missing in [None, '', ' ', '-', '?']:
            fields = reference_fields('RefSeq', missing)
            self.assertIsNone(fields['external_id'])
            self.assertIsNone(fields['url'])
        fields = reference_fields('RefSeq', 'unresolved-source-id')
        self.assertEqual(fields['external_id'], 'unresolved-source-id')
        self.assertIsNone(fields['url'])
        self.assertIsNone(fields['transcript_id_full'])

    def test_other_refseq_molecule_types(self):
        for value in ['XP_123456.1', 'YP_003024026.1']:
            self.assertIn('/protein/', identifier_url('RefSeq', value))
        for value in ['NM_123456.1', 'XR_123456.1', 'NC_000001.11']:
            self.assertIn('/nuccore/', identifier_url('RefSeq', value))

    def test_genomic_partner_is_not_falsely_labeled_as_transcript(self):
        fields = uniprot_xref_fields({'database': 'RefSeq', 'external_id': 'YP_003024031.1',
                 'properties_json': '[{"key":"NucleotideSequenceId","value":"NC_012920.1"}]'})
        self.assertEqual(fields['nucleotide_id_full'], 'NC_012920.1')
        self.assertEqual(fields['nucleotide_url'], 'https://www.ncbi.nlm.nih.gov/nuccore/NC_012920.1')
        self.assertIsNone(fields['transcript_id_full'])
        self.assertIsNone(fields['transcript_url'])


if __name__ == '__main__':
    unittest.main()
