import unittest
from tempfile import TemporaryDirectory

from xenocode.tools.math_engine import (
    MathEngine,
    MathEvaluationError,
)
from xenocode.tools.registry import build_default_registry


class MathEngineTests(unittest.TestCase):

    def setUp(self):
        self.engine = MathEngine()

    def test_basic_arithmetic(self):
        self.assertEqual(self.engine.calculate("2 + 3"), "5")

    def test_operator_precedence(self):
        self.assertEqual(self.engine.calculate("2 + 3 * 4"), "14")

    def test_parentheses(self):
        self.assertEqual(self.engine.calculate("(2 + 3) * 4"), "20")

    def test_power(self):
        self.assertEqual(self.engine.calculate("2 ** 10"), "1024")

    def test_unary_operators(self):
        self.assertEqual(self.engine.calculate("-5 + +2"), "-3")

    def test_division(self):
        self.assertEqual(self.engine.calculate("10 / 4"), "2.5")

    def test_division_by_zero(self):
        with self.assertRaises(MathEvaluationError):
            self.engine.calculate("10 / 0")

    def test_function_calls_rejected(self):
        with self.assertRaises(MathEvaluationError):
            self.engine.calculate("__import__('os')")

    def test_variable_names_rejected(self):
        with self.assertRaises(MathEvaluationError):
            self.engine.calculate("secret + 1")

    def test_boolean_rejected(self):
        with self.assertRaises(MathEvaluationError):
            self.engine.calculate("True")

    def test_comparison_rejected(self):
        with self.assertRaises(MathEvaluationError):
            self.engine.calculate("2 > 1")

    def test_large_exponent_rejected(self):
        with self.assertRaises(MathEvaluationError):
            self.engine.calculate("2 ** 1000000")

    def test_empty_expression_rejected(self):
        with self.assertRaises(MathEvaluationError):
            self.engine.calculate("   ")

    def test_long_expression_rejected(self):
        with self.assertRaises(MathEvaluationError):
            self.engine.calculate("1+" * 200)

    def test_calculator_tool_registered(self):
        with TemporaryDirectory() as workspace:
            registry = build_default_registry(workspace)

            result = registry.execute(
                "calculate",
                {"expression": "6 * 7"},
            )

            self.assertEqual(result, "42")


if __name__ == "__main__":
    unittest.main()
