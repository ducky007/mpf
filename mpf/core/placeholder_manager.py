"""Templates and placeholders."""
import ast
import operator as op
import abc

from mpf.core.mpf_controller import MpfController

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg, ast.Not: op.not_}

bool_operators = {ast.And: lambda a, b: a and b, ast.Or: lambda a, b: a or b}

comparisons = {ast.Eq: op.eq, ast.Lt: op.lt, ast.Gt: op.gt, ast.LtE: op.le, ast.GtE: op.ge, ast.NotEq: op.ne}


class BaseTemplate(metaclass=abc.ABCMeta):

    """Base class for templates."""

    def __init__(self, template, placeholder_manger, default_value):
        """Initialise template."""
        self.template = template
        self.placeholder_manager = placeholder_manger
        self.default_value = default_value

    @abc.abstractmethod
    def evaluate(self, parameters, fail_on_missing_params=False):
        """Evaluate template."""
        pass


class BoolTemplate(BaseTemplate):

    """Bool template."""

    def evaluate(self, parameters, fail_on_missing_params=False):
        """Evaluate template to bool."""
        try:
            result = self.placeholder_manager.evaluate_template(self.template, parameters)
        except ValueError:
            if fail_on_missing_params:
                raise
            return self.default_value
        return bool(result)


class FloatTemplate(BaseTemplate):

    """Float template."""

    def evaluate(self, parameters, fail_on_missing_params=False):
        """Evaluate template to float."""
        try:
            result = self.placeholder_manager.evaluate_template(self.template, parameters)
        except ValueError:
            if fail_on_missing_params:
                raise
            return self.default_value
        return float(result)


class IntTemplate(BaseTemplate):

    """Float template."""

    def evaluate(self, parameters, fail_on_missing_params=False):
        """Evaluate template to float."""
        try:
            result = self.placeholder_manager.evaluate_template(self.template, parameters)
        except ValueError:
            if fail_on_missing_params:
                raise
            return self.default_value
        return int(result)


class PlaceholderManager(MpfController):

    """Manages templates and placeholders for MPF."""

    def __init__(self, machine):
        """Initialise."""
        super().__init__(machine)
        self._eval_methods = {
            ast.Num: self._eval_num,
            ast.Str: self._eval_str,
            ast.NameConstant: self._eval_name_constant,
            ast.BinOp: self._eval_bin_op,
            ast.UnaryOp: self._eval_unary_op,
            ast.Compare: self._eval_compare,
            ast.BoolOp: self._eval_bool_op,
            ast.Attribute: self._eval_attribute,
            ast.Subscript: self._eval_subscript,
            ast.Name: self._eval_name
        }

    @staticmethod
    def _parse_template(template_str):
        return ast.parse(template_str, mode='eval').body

    def _eval_subscript2(self, node, variables):
        if isinstance(node.slice, ast.Index):
            return self._eval(node.value, variables)[self._eval(node.slice.value, variables)]
        elif isinstance(node.slice, ast.Slice):
            return self._eval(node.value, variables)[self._eval(node.slice.lower, variables):
                                                     self._eval(node.slice.upper, variables):
                                                     self._eval(node.slice.step, variables)]
        else:
            raise TypeError(type(node))

    @staticmethod
    def _eval_num(node, variables):
        del variables
        return node.n

    @staticmethod
    def _eval_str(node, variables):
        del variables
        return node.s

    @staticmethod
    def _eval_name_constant(node, variables):
        del variables
        return node.value

    def _eval_bin_op(self, node, variables):
        return operators[type(node.op)](self._eval(node.left, variables), self._eval(node.right, variables))

    def _eval_unary_op(self, node, variables):
        return operators[type(node.op)](self._eval(node.operand, variables))

    def _eval_compare(self, node, variables):
        if len(node.ops) > 1:
            raise AssertionError("Only single comparisons are supported.")
        return comparisons[type(node.ops[0])](self._eval(node.left, variables),
                                              self._eval(node.comparators[0], variables))

    def _eval_bool_op(self, node, variables):
        result = self._eval(node.values[0], variables)
        for i in range(1, len(node.values)):
            result = bool_operators[type(node.op)](result,
                                                   self._eval(node.values[i], variables))
        return result

    def _eval_attribute(self, node, variables):
        return getattr(self._eval(node.value, variables), node.attr)

    def _eval_subscript(self, node, variables):
        return self._eval_subscript2(node, variables)

    def _eval_name(self, node, variables):
        var = self.get_global_parameters(node.id)
        if var:
            return var
        elif node.id in variables:
            return variables[node.id]
        else:
            raise ValueError("Mising variable {}".format(node.id))

    def _eval(self, node, variables):
        if node is None:
            return None

        elif type(node) in self._eval_methods:  # pylint: disable-msg=unidiomatic-typecheck
            return self._eval_methods[type(node)](node, variables)
        else:
            raise TypeError(type(node))

    def build_float_template(self, template_str, default_value=0.0):
        """Build a float template from a string."""
        return FloatTemplate(self._parse_template(template_str), self, default_value)

    def build_int_template(self, template_str, default_value=0):
        """Build a int template from a string."""
        return IntTemplate(self._parse_template(template_str), self, default_value)

    def build_bool_template(self, template_str, default_value=False):
        """Build a bool template from a string."""
        return BoolTemplate(self._parse_template(template_str), self, default_value)

    def get_global_parameters(self, name):
        """Return global params."""
        if name == "settings":
            return self.machine.settings
        elif self.machine.game:
            if name == "current_player":
                return self.machine.game.player
            elif name == "players":
                return self.machine.game.player_list
            elif name == "game":
                return self.machine.game
        return False

    def evaluate_template(self, template, parameters):
        """Evaluate template."""
        return self._eval(template, parameters)
