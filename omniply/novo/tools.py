from .imports import *

from .abstract import *
from .errors import *



class MyAbstractTool(AbstractTool):
	_ToolFailedError = ToolFailedError
	_MissingGizmoError = MissingGizmoError


	def _get_from(self, ctx: AbstractContext, gizmo: str) -> Any:
		raise NotImplementedError


	def get_from(self, ctx: Optional[AbstractContext], gizmo: str,
	             default: Optional[Any] = unspecified_argument) -> Any:
		try:
			return self._get_from(ctx, gizmo)
		except self._ToolFailedError:
			if default is unspecified_argument:
				raise
			return default



class FunctionTool(MyAbstractTool):
	def __init__(self, gizmo: str, fn: Callable, **kwargs):
		super().__init__(**kwargs)
		self._gizmo = gizmo
		self._fn = fn


	def __repr__(self):
		return f'{self.__class__.__name__}({self.__call__.__name__}: {self._gizmo})'


	@property
	def __call__(self):
		return self._fn#.__get__(None, type(None))


	def __get__(self, instance, owner):
		# return self._fn.__get__(instance, owner)
		if instance is None:
			return self
		return self._fn.__get__(instance, owner)


	@staticmethod
	def _extract_gizmo_args(fn: Callable, ctx: AbstractContext,
	                        args: Optional[Tuple] = None, kwargs: Optional[Dict[str, Any]] = None) \
			-> Tuple[Tuple, Dict[str, Any]]:
		return extract_function_signature(fn, default_fn=lambda gizmo, default: ctx.get(gizmo, default))


	def _get_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		if gizmo != self._gizmo:
			raise self._MissingGizmoError(gizmo)

		args, kwargs = self._extract_gizmo_args(self._fn, ctx)
		return self._fn(*args, **kwargs)


	def gizmos(self) -> Iterator[str]:
		yield self._gizmo


	def produces_gizmo(self, gizmo: str) -> bool:
		return gizmo == self._gizmo



class ToolDecorator(MyAbstractTool):
	def __init__(self, gizmo: str, **kwargs):
		super().__init__(**kwargs)
		self._gizmo = gizmo


	def gizmos(self) -> Iterator[str]:
		yield self._gizmo


	def produces_gizmo(self, gizmo: str) -> bool:
		return gizmo == self._gizmo


	def _get_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		raise self._ToolFailedError(gizmo)


	def _actualize_tool(self, fn: Callable, **kwargs):
		return ToolCraft(self._gizmo, fn, **kwargs)


	def __call__(self, fn):
		return self._actualize_tool(fn)


class ToolSkill(FunctionTool, AbstractSkill):
	def __init__(self, gizmo: str, fn: Callable, unbound_fn: Callable, **kwargs):
		super().__init__(gizmo, fn, **kwargs)
		self._unbound_fn = unbound_fn
		

	@property
	def __call__(self):
		return self._unbound_fn
	

	def __get__(self, instance, owner):
		if instance is None:
			return self
		return self._unbound_fn.__get__(instance, owner)



class ToolCraft(FunctionTool, NestableCraft):
	_SkillCraft = ToolSkill
	def _wrapped_content(self): # wrapped method
		return self._fn


	def as_skill(self, owner: AbstractCrafty):
		return self._SkillCraft(self._gizmo,
		                        fn=self._fn.__get__(owner, type(owner)),
		                        unbound_fn=self._fn)
		return self # same instance each time _process_crafts is called




