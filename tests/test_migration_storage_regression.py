"""Frozen value behavior relevant when rebuilding a portable catalog."""
import math
import struct
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def same_typed_value(source, value, arrow_type):
    if source is None or value is None:
        return source is value
    if pa.types.is_list(arrow_type):
        return len(source) == len(value) and all(
            same_typed_value(x, y, arrow_type.value_type) for x, y in zip(source, value))
    if pa.types.is_floating(arrow_type):
        code = 'f' if arrow_type.bit_width == 32 else 'd'
        if math.isnan(source) and math.isnan(value):
            return True
        return struct.pack('!' + code, source) == struct.pack('!' + code, value)
    return source == value


class MigrationStorageRegression(unittest.TestCase):
    def test_float_precision_and_signed_zero(self):
        restored = pa.array([0.1, -0.0], type=pa.float32()).to_pylist()
        self.assertNotEqual(0.1, restored[0])
        self.assertTrue(same_typed_value(0.1, restored[0], pa.float32()))
        self.assertFalse(same_typed_value(0.1, restored[0], pa.float64()))
        self.assertTrue(same_typed_value(-0.0, restored[1], pa.float32()))
        self.assertFalse(same_typed_value(-0.0, 0.0, pa.float32()))

    def test_null_empty_nan_arrays_and_json_roundtrip(self):
        table = pa.table({
            'values': pa.array([None, [], [0.1, None, float('nan'), -0.0]],
                               type=pa.list_(pa.float32())),
            'json': pa.array(['null', '{}', '{"n":9223372036854775807,"zero":0,"nested":[null,[]]}']),
        })
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'values.parquet'
            pq.write_table(table, path)
            restored = pq.read_table(path)
            for column in range(table.num_columns):
                for original, actual in zip(table.column(column).to_pylist(),
                                            restored.column(column).to_pylist()):
                    self.assertTrue(same_typed_value(original, actual, table.schema[column].type))
            self.assertIsNone(restored['values'][0].as_py())
            self.assertEqual(restored['values'][1].as_py(), [])
            self.assertTrue(math.isnan(restored['values'][2].as_py()[2]))
            self.assertEqual(restored['json'][2].as_py(), table['json'][2].as_py())


if __name__ == '__main__':
    unittest.main()
