from typing import Any, Optional, Iterator
from .abstract import AbstractGame, AbstractGadget
from .gaggles import LoopyGaggle
from .games import CacheGame

from itertools import tee



class AbstractGraceful(AbstractGadget):
	def graces(self) -> Iterator[AbstractGadget]:
		raise NotImplementedError



class BacktrackingGaggle(LoopyGaggle):
	_grab_tree: Optional[dict[str, set[str]]]
	_grab_trace: Optional[list[str]]

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._grab_tree = {}
		self._grab_trace = []


	def _find_backtrack(self, ctx: 'AbstractGame', gizmo: str) -> Optional[list[str]]:
		itr = self._grabber_stack.get(gizmo)
		if itr is not None:
			peek, remaining = tee(itr)
			try:
				next(peek)
			except StopIteration:
				# no alternative found for candidate
				self._grabber_stack.pop(gizmo, None)
			# keep looking
			else:
				# candidate confirmed, try backtracking
				self._grabber_stack[gizmo] = remaining
				self._grab_tree.pop(gizmo, None)
				return [gizmo]

		for dependency in self._grab_tree.get(gizmo, []):
			path = self._find_backtrack(ctx, dependency)
			if path is not None:
				self._grab_tree.pop(gizmo, None)
				path.append(gizmo)
				return path


	def _attempt_backtrack(self, ctx: 'AbstractGame', gizmo: str, path: list[str]):
		return self.grab_from(ctx, gizmo)


	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
		if len(self._grab_trace):
			self._grab_tree.setdefault(self._grab_trace[-1], set()).add(gizmo)
		self._grab_trace.append(gizmo)

		try:
			out = super().grab_from(ctx, gizmo)
		except self._AssemblyFailedError as e:
			path = self._find_backtrack(ctx, gizmo)
			if path is None:
				raise
			return self._attempt_backtrack(ctx, gizmo, path)
		except self._MissingGadgetError:
			self._grab_trace.pop()
			raise
		assert self._grab_trace[-1] == gizmo, (f'Expected {gizmo!r} to be the last in the trace, '
											   f'but got {self._grab_trace[-1]!r}')
		self._grab_trace.pop()
		if len(self._grab_trace) == 0:
			self._grab_tree.clear()
		# self._grab_trace.clear()
		return out


class BacktrackingCache(CacheGame, BacktrackingGaggle):
	def _attempt_backtrack(self, ctx: 'AbstractGame', gizmo: str, path: list[str]):
		for dep in path:
			if dep in self.data:
				del self.data[dep]
		return super()._attempt_backtrack(ctx, gizmo, path)



