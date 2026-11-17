"""Safe arithmetic expression evaluator."""

import ast
import math
import operator


class MathEvaluationError(ValueError):
    """Raised when an expression is invalid or unsafe."""


class MathEngine:
    MAX_EXPRESSION_LENGTH = 256
    MAX_AST_NODES = 64
    MAX_INTEGER_BITS = 4096
    MAX_EXPONENT = 64
    MAX_FLOAT_MAGNITUDE = 1e100

    BINARY_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }

    UNARY_OPERATORS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def _check_number(self, value):
        if type(value) not in (int, float):
            raise MathEvaluationError("Only real numbers are allowed.")

        if type(value) is int:
            if value.bit_length() > self.MAX_INTEGER_BITS:
                raise MathEvaluationError("Integer result is too large.")

        elif (
            not math.isfinite(value)
            or abs(value) > self.MAX_FLOAT_MAGNITUDE
        ):
            raise MathEvaluationError("Floating-point result is out of range.")

        return value

    def _evaluate(self, node):
        if isinstance(node, ast.Constant):
            return self._check_number(node.value)

        if isinstance(node, ast.UnaryOp):
            operation = self.UNARY_OPERATORS.get(type(node.op))

            if operation is None:
                raise MathEvaluationError("Unsupported unary operator.")

            value = self._evaluate(node.operand)
            return self._check_number(operation(value))

        if isinstance(node, ast.BinOp):
            operation = self.BINARY_OPERATORS.get(type(node.op))

            if operation is None:
                raise MathEvaluationError("Unsupported binary operator.")

            left = self._evaluate(node.left)
            right = self._evaluate(node.right)

            if isinstance(node.op, ast.Pow):
                if abs(right) > self.MAX_EXPONENT:
                    raise MathEvaluationError("Exponent is too large.")

            try:
                result = operation(left, right)
            except (ArithmeticError, TypeError, ValueError) as exc:
                raise MathEvaluationError(
                    "Invalid arithmetic operation."
                ) from exc

            return self._check_number(result)

        raise MathEvaluationError("Unsupported expression.")

    def calculate(self, expression):
        if not isinstance(expression, str):
            raise MathEvaluationError("Expression must be text.")

        expression = expression.strip()

        if not expression:
            raise MathEvaluationError("Expression cannot be empty.")

        if len(expression) > self.MAX_EXPRESSION_LENGTH:
            raise MathEvaluationError("Expression is too long.")

        try:
            tree = ast.parse(expression, mode="eval")
        except (SyntaxError, ValueError) as exc:
            raise MathEvaluationError("Invalid mathematical expression.") from exc

        if sum(1 for _ in ast.walk(tree)) > self.MAX_AST_NODES:
            raise MathEvaluationError("Expression is too complex.")

        result = self._evaluate(tree.body)
        return str(result)
