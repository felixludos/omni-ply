from typing import Iterator, Optional, Any, Iterable, Callable
from omnibelt import extract_function_signature
from omnibelt.crafts import AbstractSkill, AbstractCraft, AbstractCrafty, NestableCraft

from .errors import GadgetFailed, MissingGizmo
from .abstract import AbstractGadget, AbstractGaggle, AbstractGig
from .gadgets import GadgetBase, SingleGadgetBase, FunctionGadget, AutoFunctionGadget



class ToolSkill(AbstractSkill):
	def __init__(self, *, unbound_fn: Callable, base: Optional[AbstractCraft] = None, **kwargs):
		super().__init__(**kwargs)
		self._unbound_fn = unbound_fn
		self._base = base

	def __get__(self, instance, owner):
		if instance is None:
			return self
		return self._unbound_fn.__get__(instance, owner)



class ToolCraft(FunctionGadget, NestableCraft):
	'''Used to link a method to a gizmo'''
	@property
	def __call__(self):
		'''calling a craft directly results in the wrapped function being called'''
		return self._wrapped_content_leaf()

	def __get__(self, instance, owner):
		'''when accessing crafts directly, they behave as regular methods, applying __get__ to the wrapped function'''
		return self._wrapped_content_leaf().__get__(instance, owner)

	def _wrapped_content(self): # wrapped method
		'''
		returns the wrapped function (may be a nested craft or other decorator) though

		If you want the actual function, use _wrapped_content_leaf
		'''
		return self._fn

	class _ToolSkill(FunctionGadget, ToolSkill):
		pass
	def as_skill(self, owner: AbstractCrafty) -> ToolSkill:
		'''
		When an AbstractCrafty is instantiated (ie. `owner`),
		any crafts accessible by the class (including inherited ones) can be converted to skills.

		Important, if a
		'''
		unbound_fn = self._wrapped_content_leaf()
		fn = unbound_fn.__get__(owner, type(owner))
		return self._ToolSkill(self._gizmo, fn=fn, unbound_fn=unbound_fn, base=self)



class AutoToolCraft(AutoFunctionGadget, ToolCraft):
	class _ToolSkill(AutoFunctionGadget, ToolSkill):
		pass



class ToolDecorator(GadgetBase):
	def __init__(self, gizmo: str, **kwargs):
		super().__init__(**kwargs)
		self._gizmo = gizmo


	def gizmos(self) -> Iterator[str]:
		yield self._gizmo


	def grabable(self, gizmo: str) -> bool:
		return gizmo == self._gizmo


	def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		raise self._GadgetFailed(gizmo)


	_ToolCraft = ToolCraft
	def _actualize_tool(self, fn: Callable, **kwargs):
		return self._ToolCraft(self._gizmo, fn=fn, **kwargs)


	def __call__(self, fn):
		return self._actualize_tool(fn)



class AutoToolDecorator(ToolDecorator):
	_ToolCraft = AutoToolCraft







