from typing import Any, Optional, Iterator
from collections import UserDict
from omnibelt import filter_duplicates

from .abstract import AbstractGang, AbstractGig
from .errors import GadgetError, ApplicationAmbiguityError
from .gigs import GigBase



class GangBase(GigBase, AbstractGang):
	_current_context: Optional[AbstractGig]

	def __init__(self, *, apply: Optional[dict[str, str]] = None, **kwargs):
		if apply is None:
			apply = {}
		super().__init__(**kwargs)
		self._raw_apply = apply
		self._raw_reverse_apply = None
		self._current_context = None


	def _gizmos(self) -> Iterator[str]:
		'''lists gizmos produced by self (using internal names)'''
		yield from super().gizmos()


	def gizmos(self) -> Iterator[str]:
		'''lists gizmos produced by self (using external names)'''
		for gizmo in self._gizmos():
			yield self.gizmo_to(gizmo)


	@property
	def internal2external(self) -> dict[str, str]:
		return self._raw_apply
	@internal2external.setter
	def internal2external(self, value: dict[str, str]):
		self._raw_apply = value
		self._raw_reverse_apply = None


	@property
	def external2internal(self) -> dict[str, str]:
		# return self._infer_external2internal(self._raw_apply, self.gizmoto())
		if self._raw_reverse_apply is None:
			self._raw_reverse_apply = self._infer_external2internal(self._raw_apply, self._gizmos())
		return self._raw_reverse_apply


	@staticmethod
	# @lru_cache(maxsize=None)
	def _infer_external2internal(raw: dict[str, str], products: Iterator[str]) -> dict[str, str]:
		reverse = {}
		for product in products:
			if product in raw:
				external = raw[product]
				if external in reverse:
					raise ApplicationAmbiguityError(product, [reverse[external], product])
				reverse[external] = product
		return reverse


	def gizmo_from(self, gizmo: str) -> str:
		return self.external2internal.get(gizmo, gizmo)


	def gizmo_to(self, gizmo: str) -> str:
		return self.internal2external.get(gizmo, gizmo)


	def _grab_from_fallback(self, error: GadgetError, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		return super()._grab_from_fallback(error, self._current_context, self.gizmo_to(gizmo))


	def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		if ctx is not None and ctx is not self and self._current_context is None:
			assert self._current_context is None, f'Context already set to {self._current_context}'
			self._current_context = ctx
		if ctx is self._current_context:
			gizmo = self.gizmo_from(gizmo) # convert to internal gizmo
		return super().grab_from(self, gizmo)





