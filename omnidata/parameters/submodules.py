from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Type, Iterable, Iterator
from omnibelt import unspecified_argument, get_printer
from omnibelt.crafts import AbstractCraft

from .abstract import AbstractSubmodule
from .hyperparameters import HyperparameterBase
from .building import get_builder, BuilderBase

prt = get_printer(__name__)



class SubmoduleBase(HyperparameterBase, AbstractSubmodule): # TODO: check builder for space (if none is provided)
	def __init__(self, default=unspecified_argument, *, typ=None, builder=None, **kwargs):
		super().__init__(default=default, **kwargs)
		self.typ = typ
		self.builder = builder


	def validate(self, product):
		value = super().validate(product)
		if self.typ is not None and not isinstance(value, self.typ):
			prt.warning(f'Value {value} is not of type {self.typ}')
		builder = self.get_builder()
		if builder is not None:
			return builder.validate(value)


	def get_builder(self, *args, **kwargs) -> Optional[BuilderBase]:
		if self.builder is not None:
			builder = get_builder(self.builder) if isinstance(self.builder, str) else self.builder
			return builder(*args, **kwargs)


	def build_with(self, *args, **kwargs):
		builder = self.get_builder()
		if builder is None:
			raise ValueError(f'No builder for {self}')
		return builder.build(*args, **kwargs)

	# def create_value(self, base, owner=None):  # TODO: maybe make thread-safe by using a lock
	# 	try:
	# 		return super().create_value(base, owner)
	# 	except self.MissingValueError:
	# 		builder = self.get_builder()
	# 		if builder is None:
	# 			raise
	# 		return builder.build()


##############

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



# class submodule(hparam):
# 	_registration_fn_name = 'register_submodule'



class SubmachineBase(SubmoduleBase, AbstractCraft):
	def __init__(self, default=unspecified_argument, *, application=None, **kwargs):
		super().__init__(default=default, **kwargs)
		self.application = application


	def get_builder(self) -> Optional[BuilderBase]:
		return super().get_builder(application=self.application)





