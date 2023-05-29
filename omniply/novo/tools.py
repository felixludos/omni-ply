from .imports import *

from .abstract import *
from .errors import *



class MyAbstractTool(AbstractTool):
	_ToolFailedError = ToolFailedError
	_MissingGizmoError = MissingGizmoError



class FunctionTool(MyAbstractTool):
	def __init__(self, gizmo: str, fn: Callable, **kwargs):
		super().__init__(**kwargs)
		self._gizmo = gizmo
		self._fn = fn


	def __repr__(self):
		return f'{self.__class__.__name__}({self._fn.__name__}: {self._gizmo})'


	@property
	def __call__(self):
		return self._fn


	@staticmethod
	def _extract_gizmo_args(fn: Callable, ctx: AbstractContext,
	                        args: Optional[Tuple] = None, kwargs: Optional[Dict[str, Any]] = None) \
			-> Tuple[Tuple, Dict[str, Any]]:
		return extract_function_signature(fn, default_fn=lambda gizmo, default: ctx.get(gizmo, default))


	def get_from(self, ctx: Union['AbstractContext', None], gizmo: str) -> Any:
		if gizmo != self._gizmo:
			raise self._MissingGizmoError(gizmo)

		args, kwargs = self._extract_gizmo_args(self._fn, ctx)
		return self._fn(*args, **kwargs)


	def gizmos(self) -> Iterator[str]:
		yield self._gizmo


	def produces_gizmo(self, gizmo: str) -> bool:
		return gizmo == self._gizmo



class ToolDecorator(AbstractTool):
	def __init__(self, gizmo: str, **kwargs):
		super().__init__(**kwargs)
		self._gizmo = gizmo


	def _actualize_tool(self, fn: Callable, **kwargs):
		return FunctionTool(self._gizmo, fn, **kwargs)


	def __call__(self, fn: Callable):
		return self._actualize_tool(fn)







