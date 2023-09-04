from typing import Any, Optional, Iterator
from collections import UserDict
from omnibelt import filter_duplicates

from .abstract import AbstractGadget, AbstractGaggle, AbstractGig
from .errors import GadgetError, MissingGizmo, AssemblyError, GigError
from .gadgets import GadgetBase



class GigBase(GadgetBase, AbstractGig):
	_GigFailedError = GigError
	def _grab_from_fallback(self, error: GadgetError, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		if ctx is None or ctx is self:
			raise self._GigFailedError(gizmo, error) from error
		return ctx.grab(gizmo)


	def _grab(self, gizmo: str) -> Any:
		return super().grab_from(self, gizmo)


	def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		try:
			out = self._grab(gizmo)
		except self._GadgetFailedError as error:
			out = self._grab_from_fallback(error, ctx, gizmo)
		return self.package(out, gizmo=gizmo)


	def package(self, val: Any, *, gizmo: Optional[str] = None) -> Any:
		return val



class CacheGig(GigBase, UserDict):
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


	def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		if self.is_cached(gizmo):
			return self.data[gizmo]
		val = super().grab_from(ctx, gizmo)
		self.data[gizmo] = val  # cache loaded val
		return val





