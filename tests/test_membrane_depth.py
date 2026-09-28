"""The sequence view must preserve OPM model values, missing depth and PDB numbering."""
import unittest
from unittest.mock import patch
from Web.src.api.membrane_overview import membrane_sequence


class MembraneDepthTests(unittest.TestCase):
    def test_models_missing_depth_and_insertion_codes_are_not_collapsed(self):
        base = dict(position=10, residue='G', pdb_id='1abc', chain_id='B',
                    source_position=42, insertion_code='A', geometry_type='dual_flat',
                    mapping_method='verified', site_coordinate_basis='ca_fallback', pdb_residue='GLY')
        rows = [{**base, 'model_id': model, 'site_signed_depth_A': depth}
                for model, depth in [(1, 0.0), (2, None), (3, -2.5)]]
        with patch('Web.src.api.membrane_overview.membrane_summary_data', return_value={
                'sequence_id': 'PTEST', 'accession': 'PTEST', 'uniprot': {'features': []}}), \
             patch('Web.src.api.membrane_overview.one', return_value={'sequence': 'G' * 10, 'length': 10}), \
             patch('Web.src.api.membrane_overview.query', side_effect=[rows, [], []]):
            projection = membrane_sequence('PTEST')
        position = projection['opm']['positions'][0]
        self.assertEqual(position['record_count'], 3)
        observations = position['structures'][0]['observations']
        self.assertEqual([(o['model'], o['depth']) for o in observations], [(1, 0.0), (2, None), (3, -2.5)])
        self.assertTrue(all(o['source_position'] == '42A' for o in observations))
        self.assertTrue(all(o['basis'] == 'ca_fallback' for o in observations))


if __name__ == '__main__':
    unittest.main()
