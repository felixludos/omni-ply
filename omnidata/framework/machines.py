from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Type, Iterable, Iterator
from collections import OrderedDict
from omnibelt import split_dict, unspecified_argument, OrderedSet, get_printer, \
	extract_function_signature, method_wrapper, agnostic

from .hyperparameters import Hyperparameter, Parameterized, hparam, Specced
from .building import get_builder, Builder, MultiBuilder, AutoClassBuilder

from omnibelt.nodes import AutoTreeNode

prt = get_printer(__name__)


class Machine(Hyperparameter, Specced):
	def __init__(self, default=unspecified_argument, *, required=True, type=None, builder=None, cache=True, **kwargs):
		super().__init__(default=default, required=required, cache=cache, **kwargs)
		self.type = type
		self.builder = builder


	def copy(self, *, type=unspecified_argument, builder=unspecified_argument, **kwargs):
		if type is unspecified_argument:
			type = self.type
		if builder is unspecified_argument:
			builder = self.builder
		return super().copy(type=type, builder=builder, **kwargs)

	def validate_value(self, value):
		if self.type is not None and not isinstance(value, self.type):
			prt.warning(f'Value {value} is not of type {self.type}')

	def get_builder(self) -> Builder:
		if self.builder is not None:
			return get_builder(self.builder) if isinstance(self.builder, str) else self.builder
	
	@agnostic
	def full_spec(self, spec=None):
		spec = super().full_spec(spec=spec)
		builder = self.get_builder()
		if builder is not None:
			spec.include(builder)
		return spec


class MachineParametrized(Parameterized):
	Machine = Machine


	@agnostic
	def register_machine(self, name=None, _instance=None, **kwargs):
		if _instance is None:
			_instance = self.Machine(name=name, **kwargs)
		return self.register_hparam(name, _instance, **kwargs)


	@agnostic
	def machines(self):
		for key, val in self.named_machines():
			yield val


	@agnostic
	def named_machines(self):
		for key, val in self.named_hyperparameters():
			if isinstance(val, Machine):
				yield key, val
	
	
	# @agnostic
	# def full_spec(self, fmt='{}', fmt_rule='{parent}.{child}', include_machines=True):
	# 	for key, val in self.named_hyperparameters():
	# 		ident = fmt.format(key)
	# 		if isinstance(val, Machine):
	# 			builder = val.get_builder()
	# 			if include_machines or builder is None:
	# 				yield ident, val
	# 			if builder is not None:
	# 				if isinstance(builder, MachineParametrized):
	# 					yield from builder.full_spec(fmt=fmt_rule.format(parent=ident, child='{}'), fmt_rule=fmt_rule)
	# 				else:
	# 					for k, v in builder.plan():
	# 						yield fmt_rule.format(parent=ident, child=k), v
	# 		else:
	# 			yield ident, val



class machine(hparam):
	_registration_fn_name = 'register_machine'


# class ModifyableBuilder(Builder):
# 	@staticmethod
# 	def realize(product, *args, **kwargs):
# 		return product(*args, **kwargs)

