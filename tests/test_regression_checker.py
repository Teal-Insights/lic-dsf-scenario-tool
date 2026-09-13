import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location(
    "regression_checker", Path(__file__).resolve().parents[1] / "scripts" / "verify_official_example.py")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class RegressionCheckerTests(unittest.TestCase):
    def test_preserves_locked_absolute_tolerance(self):
        self.assertEqual(CHECKER.compare(2.0, 2.0 + 1e-7), 1)
        with self.assertRaises(ValueError):
            CHECKER.compare(2.0, 2.0 + 1e-5)

    def test_rejects_missing_or_extra_fields_and_shortened_lists(self):
        for expected, actual in [({"x": 1}, {}), ({}, {"x": 1}), ([1, 2], [1])]:
            with self.subTest(expected=expected, actual=actual), self.assertRaises(ValueError):
                CHECKER.compare(expected, actual)

    def test_boolean_is_not_a_numeric_match(self):
        with self.assertRaises(ValueError):
            CHECKER.compare(1, True)
        with self.assertRaises(ValueError):
            CHECKER.compare(False, 0)

    def test_nonfinite_values_and_changed_error_classes_fail(self):
        for expected, actual in [(1.0, float("nan")), (float("inf"), float("inf")),
                                 ("#N/A", "#VALUE!"), (None, 0)]:
            with self.subTest(expected=expected, actual=actual), self.assertRaises(ValueError):
                CHECKER.compare(expected, actual)

    def test_checks_every_leaf_and_identifies_first_mismatch(self):
        data = {"points": [{"value": 1}, {"value": "#N/A"}], "missing": None}
        self.assertEqual(CHECKER.compare(data, data), 3)
        with self.assertRaisesRegex(ValueError, r"result.points\[1\].value"):
            CHECKER.compare(data, {"points": [{"value": 1}, {"value": "#VALUE!"}], "missing": None})


if __name__ == "__main__":
    unittest.main()
