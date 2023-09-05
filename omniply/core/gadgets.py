from typing import Iterator, Optional, Any, Iterable, Callable
from omnibelt import extract_function_signature
from omnibelt.crafts import AbstractSkill, NestableCraft

from .errors import GadgetError, MissingGizmo
from .abstract import AbstractGadget, AbstractGaggle, AbstractGig



class GadgetBase(AbstractGadget):
	_GadgetError = GadgetError
	_MissingGizmoError = MissingGizmo



class SingleGadgetBase(GadgetBase):
	'''A gadget that only grabs a single gizmo, specified at init'''
	def __init__(self, gizmo: str, **kwargs):
		super().__init__(**kwargs)
		self._gizmo = gizmo

	def gizmos(self) -> Iterator[str]:
		yield self._gizmo



class FunctionGadget(SingleGadgetBase):
	'''
	A gadget that grabs a single gizmo using a given function, both specified at init.

	The function should take a single argument, the gig, and returns the gizmo.
	'''
	def __init__(self, gizmo: str, fn: Callable, **kwargs):
		super().__init__(gizmo=gizmo, **kwargs)
		self._fn = fn

	def __repr__(self):
		name = getattr(self._fn, '__qualname__', None)
		if name is None:
			name = getattr(self._fn, '__name__', None)
		return f'{self.__class__.__name__}({name}: {self._gizmo})'

	@property
	def __call__(self):
		return self._fn

	def __get__(self, instance, owner):
		return self._fn.__get__(instance, owner)

	def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		if gizmo != self._gizmo:
			raise self._MissingGizmoError(gizmo)
		return self._fn(ctx)



class AutoFunctionGadget(FunctionGadget):
	'''
	A gadget that grabs a single gizmo using a given function, both specified at init.

	The function can take any number of arguments, and any arguments that are gizmos
	will be grabbed from the gig automatically.
	'''
	@staticmethod
	def _extract_gizmo_args(fn: Callable, ctx: AbstractGig, *, args: Optional[tuple] = None,
							kwargs: Optional[dict[str, Any]] = None) -> tuple[list[Any], dict[str, Any]]:
		return extract_function_signature(fn, args=args, kwargs=kwargs, default_fn=ctx.grab)

	def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		if gizmo != self._gizmo:
			raise self._MissingGizmoError(gizmo)

		args, kwargs = self._extract_gizmo_args(self._fn, ctx)
		return self._fn(*args, **kwargs)




