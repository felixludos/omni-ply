from typing import Any, Optional, Iterator
from collections import UserDict
from omnibelt import filter_duplicates

from .abstract import AbstractGroup, AbstractGig
from .errors import GadgetError, ApplicationAmbiguityError
from .gaggles import GaggleBase
from .gigs import GigBase, GroupCache



class GroupBase(GaggleBase, AbstractGroup):
	_current_context: Optional[AbstractGig]

	def __init__(self, *args, gap: Optional[dict[str, str]] = None, **kwargs):
		if gap is None:
			gap = {}
		super().__init__(*args, **kwargs)
		self._raw_gap = gap
		self._raw_reverse_gap = None
		self._gig_stack = []
		# self._current_context = None


	def _gizmos(self) -> Iterator[str]:
		'''lists gizmos produced by self (using internal names)'''
		yield from super().gizmos()


	def gizmos(self) -> Iterator[str]:
		'''lists gizmos produced by self (using external names)'''
		for gizmo in self._gizmos():
			yield self.gizmo_to(gizmo)


	@property
	def internal2external(self) -> dict[str, str]:
		return self._raw_gap
	@internal2external.setter
	def internal2external(self, value: dict[str, str]):
		self._raw_gap = value
		self._raw_reverse_gap = None


	@property
	def external2internal(self) -> dict[str, str]:
		# return self._infer_external2internal(self._raw_apply, self.gizmoto())
		if self._raw_reverse_gap is None:
			self._raw_reverse_gap = self._infer_external2internal(self._raw_gap, self._gizmos())
		return self._raw_reverse_gap


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


	def _grab(self, gizmo: str):
		return super().grab_from(self, gizmo)


	def grab_from(self, ctx: AbstractGig, gizmo: str) -> Any:
		if ctx is not None and ctx is not self:
			self._gig_stack.append(ctx)
			gizmo = self.gizmo_from(gizmo) # convert to internal gizmo

		try:
			out = self._grab(gizmo)
		except self._GadgetError:
			if len(self._gig_stack) == 0 or ctx is self._gig_stack[-1]:
				raise
			# default to parent/s
			out = self._gig_stack[-1].grab(self.gizmo_to(gizmo))

		if len(self._gig_stack) and ctx is self._gig_stack[-1]:
			self._gig_stack.pop()

		return out

	# def _grab_from_fallback(self, error: Exception, ctx: Optional[AbstractGig], gizmo: str) -> Any:
	# 	assert ctx is self, f'{ctx} != {self}'
	# 	if len(self._gig_stack):
	# 		return super()._grab_from_fallback(error, self._gig_stack[-1], self.gizmo_to(gizmo))
	# 	raise error from error
	#
	#
	# def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
	# 	if ctx is not None and ctx is not self:
	# 		self._gig_stack.append(ctx)
	# 		gizmo = self.gizmo_from(gizmo) # convert to internal gizmo
	# 	out = super().grab_from(self, gizmo)
	# 	if len(self._gig_stack) and ctx is self._gig_stack[-1]:
	# 		self._gig_stack.pop()
	# 	return out



class CachableGroup(GroupBase):
	_GroupCacheMiss = KeyError
	def _grab(self, gizmo: str) -> Any:
		if len(self._gig_stack):
			# check cache (if one exists)
			for parent in reversed(self._gig_stack):
				if isinstance(parent, GroupCache):
					try:
						return parent.check_group_cache(self, gizmo)
					except self._GroupCacheMiss:
						pass

			# if it cant be found in my cache, check the cache using the external gizmo name
			ext = self.gizmo_to(gizmo)
			for parent in reversed(self._gig_stack):
				if isinstance(parent, GroupCache) and parent.is_cached(ext):
					return parent.grab(ext)

		# if it cant be found in any cache, grab it from my gadgets
		out = super()._grab(gizmo)

		# update my cache
		if len(self._gig_stack):
			for parent in reversed(self._gig_stack):
				if isinstance(parent, GroupCache):
					parent.update_group_cache(self, gizmo, out)
					break

		return out



class SelectiveGroup(GroupBase):
	def __init__(self, *args, gap: dict[str, str] | list[str] | None = None, **kwargs):
		if isinstance(gap, list):
			gap = {gizmo: gizmo for gizmo in gap}
		if isinstance(gap, dict):
			gap = {gizmo: gizmo if ext is None else ext for gizmo, ext in gap.items()}
		super().__init__(*args, gap=gap, **kwargs)


	def gizmos(self) -> Iterator[str]:
		'''lists gizmos produced by self (using external names)'''
		for gizmo in self._gizmos():
			if gizmo in self.internal2external:
				yield self.gizmo_to(gizmo)




