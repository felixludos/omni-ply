from typing import Any, Optional, Iterator, Union, Tuple
from .errors import GrabError
from .abstract import AbstractGame, AbstractGadget
from .gaggles import LoopyGaggle
from .games import CacheGame

from itertools import tee, chain



class AbstractGrace:
	def grace_grab(self, error: GrabError, ctx: AbstractGame, gizmo: str) -> Any:
		raise NotImplementedError



class AbstractGraceful(AbstractGadget):
	def grace(self, gizmo: str) -> Optional[AbstractGrace]:
		raise NotImplementedError



class GracefulGaggle(LoopyGaggle):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._grab_tree = {}
		self._grab_trace = []
		self._grab_gadgets = {} # need to track which gadgets were already used for potential graces (when backtracking)

	def _ask_for_grace(self, gadget: Union[AbstractGadget, AbstractGrace], gizmo: str) \
			-> Optional[Tuple[AbstractGrace, list[str]]]:
		if isinstance(gadget, AbstractGraceful):
			grace = gadget.grace(gizmo)
			if grace is not None:
				return grace, [gizmo]

		for dependency in self._grab_tree.get(gizmo, []):
			option = self._ask_for_grace(ctx, dependency, None, e)
			if option is not None:
				grace, path = option
				self._grab_tree.pop(gizmo, None)
				path.append(gizmo)
				return grace, path

	def _graceful_grab(self, error: GrabError, ctx: AbstractGame, grace: AbstractGrace, path: list[str]) -> Any:
		# (clear cache as necessary based on path)

		# curry the error into the grace grab, and then chain the grace with the current grabber_stack[path[0]]
		# clear the grabber stack for the current path[1:]
		# then return self.grab_from(ctx, path[-1])
		raise NotImplementedError



	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the context using the gadgets in the _grabber_stack dictionary.

		Args:
			ctx (AbstractGame): The context with which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.

		Raises:
			AssemblyFailedError: If all gadgets fail to produce the gizmo.
			MissingGadgetError: If no gadget can produce the gizmo.
		"""
		if len(self._grabber_stack) == 0:
			self._grab_query = gizmo

		if gizmo in self._grab_graces:
			itr = self._grab_graces[gizmo]

			try:
				gadget = next(itr)
			except StopIteration:
				raise

		else:
			itr = self._grabber_stack.setdefault(gizmo, self._gadgets(gizmo))

			try:
				gadget = next(itr)
			except StopIteration:
				raise self._MissingGadgetError(gizmo)

		try:
			out = gadget.grab_from(ctx, gizmo)
		except self._GadgetFailure as e:
			return self._ask_for_grace(ctx, gizmo, gadget, e)
		except:
			logger.debug(f'{gadget!r} failed while trying to produce {gizmo!r}')
			raise

		if gizmo == self._grab_query:
			# self._grab_query = None
			self._grabber_stack.clear()
		return out



class BacktrackingGaggle(LoopyGaggle):
	_grab_tree: Optional[dict[str, set[str]]]
	_grab_trace: Optional[list[str]]
	_grab_graces: Optional[dict[str, Iterator[AbstractGadget]]]

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._grab_tree = {}
		self._grab_trace = []
		self._grab_graces = {}


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



