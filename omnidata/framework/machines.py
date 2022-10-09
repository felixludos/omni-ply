from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Type, Iterable, Iterator
from collections import OrderedDict
from omnibelt import split_dict, unspecified_argument, agnosticmethod, OrderedSet, \
	extract_function_signature, method_wrapper, agnostic

from .hyperparameters import Hyperparameter, Parameterized, hparam
from .building import get_builder, Builder, ClassBuilder, AutoClassBuilder

from omnibelt.nodes import AutoTreeNode



class Machine(Hyperparameter):
	def __init__(self, default=unspecified_argument, required=True, type=None, builder=None,
	             cache=None, ref=None, **kwargs):
		if ref is not None:
			if type is None:
				type = ref.type
			if builder is None:
				builder = ref.builder
		if cache is None:
			cache = type is not None or builder is not None
		super().__init__(default=default, required=required, cache=cache, ref=ref, **kwargs)
		self.type = type
		self.builder = builder


	class InvalidValue(Hyperparameter.InvalidValue):
		def __init__(self, name, value, base, msg=None):
			if msg is None:
				value = type(value) if isinstance(value, type) else str(value)
				msg = f'{name}: {value} (expecting an instance of {base})'
			super().__init__(name, value, msg=msg)
			self.base = base


	def get_builder(self) -> Builder:
		if self.builder is not None:
			return get_builder(self.builder) if isinstance(self.builder, str) else self.builder
		if self.type is not None and isinstance(self.type, Builder):
			return self.type



class MachineParametrized(Parameterized):
	Machine = Machine


	# @agnostic
	# def _extract_hparams(self, kwargs):
	# 	found, remaining = split_dict(kwargs, self._registered_hparams)
	# 	for key, val in found.items():
	# 		setattr(self, key, val)
	# 	return remaining


	@agnosticmethod
	def register_machine(self, name=None, _instance=None, **kwargs):
		if _instance is None:
			_instance = self.Machine(name=name, **kwargs)
		return self.register_hparam(name, _instance)


	@agnosticmethod
	def machines(self):
		for key, val in self.named_machines():
			yield val


	@agnosticmethod
	def named_machines(self):
		for key, val in self.named_hyperparameters():
			if isinstance(val, Machine):
				yield key, val


	@agnosticmethod
	def full_spec(self, fmt='{}', fmt_rule='{parent}.{child}', include_machines=True):
		for key, val in self.named_hyperparameters():
			ident = fmt.format(key)
			if isinstance(val, Machine):
				builder = val.get_builder()
				if include_machines or builder is None:
					yield ident, val
				if builder is not None:
					if isinstance(builder, MachineParametrized):
						yield from builder.full_spec(fmt=fmt_rule.format(parent=ident, child='{}'), fmt_rule=fmt_rule)
					else:
						for k, v in builder.plan():
							yield fmt_rule.format(parent=ident, child=k), v
			else:
				yield ident, val



class machine(hparam):
	_registration_fn_name = 'register_machine'


# class ModifyableBuilder(Builder):
# 	@staticmethod
# 	def realize(product, *args, **kwargs):
# 		return product(*args, **kwargs)

