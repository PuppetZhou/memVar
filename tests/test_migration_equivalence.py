"""Guard acceptance comparison against silent loss of scientific/API semantics."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('migration_equivalence',Path(__file__).with_name('migration_equivalence.py'))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class EquivalenceComparatorTest(unittest.TestCase):
    def test_false_does_not_equal_real_zero(self):
        self.assertTrue(module.differences({'af':0},{'af':False}))

    def test_missing_field_does_not_equal_null(self):
        self.assertTrue(module.differences({'score':None},{}))

    def test_array_order_is_preserved(self):
        self.assertTrue(module.differences({'ids':['a-2','a-10']},{'ids':['a-10','a-2']}))

    def test_json_object_key_order_is_irrelevant(self):
        self.assertFalse(module.differences({'a':None,'b':[0.0,-1.2]},{'b':[0.0,-1.2],'a':None}))

if __name__=='__main__':unittest.main()
