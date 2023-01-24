from typing import Type, Callable, Any
import inspect

from .abstract import AbstractContext
from .base import RawCraft, CraftTool



class MachineBase(CraftTool):
	@staticmethod
	def _parse_context_args(fn: Callable, ctx: AbstractContext):
		# TODO: allow for default values -> use omnibelt extract_signature

		args = {}
		params = inspect.signature(fn).parameters
		for name, param in params.items():
			if name in ctx:
				args[name] = ctx[name]

		return args


	def send_get_from(self, instance: Any, ctx: AbstractContext, gizmo: str) -> Any:
		getter_fn = self._find_getter_fn(instance, gizmo)
		return getter_fn(**self._parse_context_args(getter_fn, ctx))



class Machine(MachineBase):
	pass



class machine(RawCraft):
	_CraftItem = Machine



class Indicator(Machine):

	@operation.log
	def send_log(self, instance: Any, ctx: AbstractContext, gizmo: str) -> Any:
		getter_fn = self._find_getter_fn(instance, gizmo)
		return getter_fn(**self._parse_context_args(getter_fn, ctx))

	pass



class indicator(machine): # outputs are all scalars
	_CraftItem = Indicator



