from .imports import *
from .abstract import *
from .kits import *



class Context(AbstractContext):
	def get(self, gizmo: str, default: Any = unspecified_argument):
		try:
			return self.get_from(None, gizmo)
		except ToolFailedError:
			if default is unspecified_argument:
				raise
			return default


	def __getitem__(self, item):
		return self.get(item)


	def _get_from_fallback(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		return ctx.get_from(self, gizmo)


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		try:
			return super().get_from(self, gizmo)
		except ToolFailedError:
			if ctx is None or ctx is self:
				raise
			return self._get_from_fallback(ctx, gizmo)



class Cached(AbstractContext, UserDict):
	def __repr__(self):
		gizmos = [(gizmo if self.is_cached(gizmo) else '{' + gizmo + '}') for gizmo in self.gizmos()]
		return f'{self.__class__.__name__}({", ".join(gizmos)})'


	def gizmos(self) -> Iterator[str]:
		yield from filter_duplicates(self.cached(), super().gizmos())


	def is_cached(self, gizmo: str) -> bool:
		return gizmo in self.data


	def cached(self) -> Iterator[str]:
		yield from self.data.keys()


	def clear_cache(self) -> None:
		self.data.clear()


	def _find_from(self, ctx: AbstractContext, gizmo: str) -> Any:
		val = super().get_from(ctx, gizmo)
		self.data[gizmo] = val  # cache loaded val
		return val


	def get_from(self, ctx: Optional[AbstractContext], gizmo: str) -> Any:
		val = self.data[gizmo] if self.is_cached(gizmo) else self._find_from(ctx, gizmo)
		return val






