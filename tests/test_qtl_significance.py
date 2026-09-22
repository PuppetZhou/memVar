import unittest
from Web.src.api.evidence_context import qtl_source_assessment

class QtlSignificanceTest(unittest.TestCase):
    def test_gtex_inclusive_and_record_specific(self):
        self.assertEqual(qtl_source_assessment('GTEx', {'pval_nominal': 1e-5, 'pval_nominal_threshold': 1e-5})['status'], 'met')
        self.assertEqual(qtl_source_assessment('GTEx', {'pval_nominal': 1e-5, 'pval_nominal_threshold': 1e-6})['status'], 'not_met')

    def test_eqtlgen_uses_fdr_not_nominal_p(self):
        self.assertEqual(qtl_source_assessment('eQTLGen', {'Pvalue': 1e-20, 'FDR': .05})['status'], 'not_met')
        self.assertEqual(qtl_source_assessment('eQTLGen', {'FDR': .049})['status'], 'met')

    def test_missing_invalid_and_zero(self):
        for value in [None, '', 'NA', float('nan'), float('inf'), -1, 2, True]:
            self.assertEqual(qtl_source_assessment('eQTLGen', {'FDR': value})['status'], 'unavailable')
        self.assertEqual(qtl_source_assessment('eQTLGen', {'FDR': 0})['status'], 'met')
        self.assertEqual(qtl_source_assessment('GTEx', {'pval_nominal': 0})['status'], 'unavailable')

    def test_qtlbase_has_no_inferred_criterion(self):
        self.assertEqual(qtl_source_assessment('QTLbase', {'Pvalue': 1e-30})['status'], 'unavailable')

if __name__ == '__main__':
    unittest.main()
