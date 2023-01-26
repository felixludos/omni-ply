from typing import Type, Callable, Any
import inspect

from omnibelt import auto_operation as operation

from .abstract import AbstractContext
from .base import GetterTool, GetterRawCraft
from .spaced import SpatialRawCraft



class MachineBase(GetterTool):
	@staticmethod
	def _parse_context_args(fn: Callable, ctx: AbstractContext):
		# TODO: allow for default values -> use omnibelt extract_signature

		args = {}
		params = inspect.signature(fn).parameters
		for name, param in params[1:].items():
			if name in ctx:
				args[name] = ctx[name]

		return args


	def send_get_from(self, instance: Any, ctx: AbstractContext, gizmo: str) -> Any:
		fn = getattr(instance, self._data['name'])
		return fn(**self._parse_context_args(fn, ctx))



class Machine(MachineBase):
	pass



class machine(SpatialRawCraft, GetterRawCraft):
	_CraftItem = Machine



class Indicator(Machine):
	@operation.log
	def send_log(self, instance: Any, ctx: AbstractContext, gizmo: str) -> Any:
		raise NotImplementedError



class indicator(machine): # outputs are all scalars
	_CraftItem = Indicator



