from .imports import *

from .abstract import *



class MyAbstractTool(AbstractTool):
	_ToolFailedError = ToolFailedError
	_MissingGizmoError = MissingGizmoError



class FunctionTool(MyAbstractTool):
	def __init__(self, gizmo: str, fn: Callable, **kwargs):
		super().__init__(**kwargs)
		self._gizmo = gizmo
		self._fn = fn

	@property
	def __call__(self):
		return self._fn


	def get_from(self, ctx: Union['AbstractContext', None], gizmo: str) -> Any:
		if gizmo != self._gizmo:
			raise self._MissingGizmoError(gizmo)



		return self._fn(ctx)


	def gizmos(self) -> Iterator[str]:
		yield self._gizmo


	def produces_gizmo(self, gizmo: str) -> bool:
		return gizmo == self._gizmo



class Tool(AbstractTool):
	def __init__(self, gizmo: str, **kwargs):
		super().__init__(**kwargs)
		self._gizmo = gizmo


	def _actualize_tool(self, fn: Callable, **kwargs):
		return FunctionTool(self._gizmo, fn, **kwargs)


	def __call__(self, fn: Callable):
		return self._actualize_tool(fn)







