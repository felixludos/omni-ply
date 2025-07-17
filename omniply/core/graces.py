from typing import Any, Optional, Iterator, Union, Tuple, Iterable, Reversible
from .errors import GrabError, SkipGadget
from .abstract import AbstractGame, AbstractGadget
from .gaggles import GaggleBase, LoopyGaggle
from .games import CacheGame

from itertools import tee, chain
from functools import partial


class AbstractGrace(AbstractGadget):
	def attach_error(self, error: GrabError) -> AbstractGadget:
		return self



class AbstractGraceful(AbstractGadget):
	def grace(self, gizmo: str) -> Optional[AbstractGrace]:
		raise NotImplementedError



class IgnorantGrace(AbstractGrace):
	def __init__(self, gadget: AbstractGadget, **kwargs):
		super().__init__(**kwargs)
		self._gadget = gadget

	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
		return self._gadget.grab_from(ctx, gizmo)



class AutoSkipGraceful(AbstractGraceful):
	class _Grace(AbstractGrace):
		def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
			raise SkipGadget

	def grace(self, gizmo: str) -> Optional[AbstractGrace]:
		return self._Grace()



class GracefulRepeater(AbstractGraceful):
	class _Grace(IgnorantGrace, AbstractGraceful):
		def __init__(self, gadget: AbstractGadget, repeat: int = 0, **kwargs):
			"""
			Initializes a SimpleRepeater gadget that repeats the grace grab.

			Args:
				gadget (AbstractGadget): The gadget to repeat.
				**kwargs: Arbitrary keyword arguments for superclasses.
			"""
			super().__init__(gadget, **kwargs)
			self.repeat = repeat

		def gives(self, gizmo: str) -> bool:
			if self._gadget is not None:
				return self._gadget.gives(gizmo)
			return super().gives(gizmo)

		def gizmos(self) -> Iterator[str]:
			if self._gadget is not None:
				yield from self._gadget.gizmos()
			else:
				yield from super().gizmos()

		def grace(self, gizmo: str, **kwargs) -> Optional[AbstractGrace]:
			if self.repeat > 0:
				return self.__class__(self._gadget, repeat=self.repeat - 1, **kwargs)

	def __init__(self, *, repeat: int = 0, **kwargs):
		super().__init__(**kwargs)
		self.repeat = repeat

	def grace(self, gizmo: str) -> Optional[AbstractGrace]:
		if self.repeat > 0:
			return self._Grace(self, self.repeat - 1)
		# elif self._payload is not None and self._payload.repeat > 0:
		# 	raise NotImplementedError(f'should return a simple gadget that raises an error that all repeats failed')


# class SimpleRepeater(AbstractGraceful):
# 	def __init__(self, repeat: int = 0, payload: Optional[AbstractGadget] = None, **kwargs):
# 		"""
# 		Initializes a GracefulRepeater gadget that repeats the grace grab a specified number of times.
#
# 		Args:
# 			repeat (int): The number of times to repeat the grace grab.
# 			**kwargs: Arbitrary keyword arguments for superclasses.
# 		"""
# 		super().__init__(**kwargs)
# 		self.repeat = repeat
# 		self._payload = payload
#
# 	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
# 		if self._payload is None:
# 			return super().grab_from(ctx, gizmo)
# 		return self._payload.grab_from(ctx, gizmo)
#
# 	def gives(self, gizmo: str) -> bool:
# 		if self._payload is not None:
# 			return self._payload.gives(gizmo)
# 		return super().gives(gizmo)
#
# 	def gizmos(self) -> Iterator[str]:
# 		if self._payload is not None:
# 			yield from self._payload.gizmos()
# 		else:
# 			yield from super().gizmos()
#
# 	def grace(self, gizmo: str) -> Optional[AbstractGrace]:
# 		if self.repeat > 0:
# 			return IgnorantGrace(SimpleRepeater(self.repeat - 1, self._payload or self))
# 		# elif self._payload is not None and self._payload.repeat > 0:
# 		# 	raise NotImplementedError(f'should return a simple gadget that raises an error that all repeats failed')



class GracefulGaggle(GaggleBase):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._grab_tree = {}
		self._grab_trace = []
		self._grabber_stack = {}
		self._grab_query = None

	def _ask_for_grace(self, ctx: AbstractGame, error: GrabError, gadget: AbstractGadget, keys: Reversible[str]) \
			-> Optional[list[Tuple[str, AbstractGadget]]]:
		gizmo = next(reversed(keys))
		if isinstance(gadget, AbstractGraceful):
			grace = gadget.grace(gizmo)
			if grace is not None:
				# curry the error into the grace grab, and then chain the grace with the current grabber_stack[path[0]]
				gadget = grace.attach_error(error)
				self._grab_tree.pop(tuple(keys), None)  # remove the current keys from the grab tree
				return [(gizmo, gadget)]

		for parent, parent_gadget in self._grab_tree.get(tuple(keys), []):
			path = self._ask_for_grace(ctx, error, parent_gadget, (*keys, parent))
			if path is not None:
				break
		else:
			return None
		self._grab_tree.pop(tuple(keys), None)
		path.append((gizmo, gadget))
		return path


	def _graceful_grab(self, path: list[Tuple[str, AbstractGadget]],
					   error: GrabError, ctx: AbstractGame, gizmo: str) -> Any:
		# # (clear cache as necessary based on path)
		# base_gizmo, grace = path[0][1]
		# assert isinstance(grace, AbstractGrace), f'Expected grace to be an instance of AbstractGrace, but got {grace!r}'
		# # curry the error into the grace grab, and then chain the grace with the current grabber_stack[path[0]]
		# gadget = partial(grace.grace_grab, error)
		#
		# path[0] = (base_gizmo, gadget)  # replace the gadget with the curried grace in the path

		# now prepend the successful gadgets into the grabber stack
		for target, gadget in path:
			assert target in self._grabber_stack, f'Expected {target!r} to be in the grabber stack, but got {self._grabber_stack!r}'
			self._grabber_stack[target] = chain([gadget], self._grabber_stack.get(target, []))

		# then return self.grab_from(ctx, path[-1])
		return self.grab_from(ctx, gizmo)


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
		if len(self._grab_trace) == 0:
			self._grab_query = gizmo
			self._grab_tree.clear()
			self._grabber_stack.clear()
		self._grab_trace.append(gizmo)

		itr = self._grabber_stack.setdefault(gizmo, self._gadgets(gizmo))

		try:
			gadget = next(itr)
		except self._MissingGadgetError:
			self._grab_trace.pop() # failed to grab the gizmo, so pop it from the trace
			raise
		except StopIteration:
			self._grab_trace.pop() # failed to grab the gizmo, so pop it from the trace
			raise self._MissingGadgetError(gizmo)

		try:
			result = gadget.grab_from(ctx, gizmo)

		except SkipGadget:
			result = self.grab_from(ctx, gizmo)

		except self._GadgetFailure as error:
			# attempt backtracking
			grace_path = self._ask_for_grace(ctx, error, gadget, tuple(self._grab_trace))
			if grace_path is None:
				self._grab_trace.pop() # failed to grab the gizmo, so pop it from the trace
				raise error
			result = self._graceful_grab(grace_path, error, ctx, gizmo)

		# except:
		# 	logger.debug(f'{gadget!r} failed while trying to produce {gizmo!r}')
		# 	raise

		assert self._grab_trace[-1] == gizmo, (f'Expected {gizmo!r} to be the last in the trace, '
											   f'but got {self._grab_trace[-1]!r}')
		self._grab_trace.pop() # completed gizmo, so pop it from the trace
		self._grab_tree.setdefault(tuple(self._grab_trace), []).append((gizmo, gadget)) # update grab tree

		# if len(self._grab_trace) == 0:
		# 	self._grab_tree.clear()
		# 	self._grabber_stack.clear()
		return result


class GracefulCache(CacheGame, GracefulGaggle):
	# def _attempt_backtrack(self, ctx: 'AbstractGame', gizmo: str, path: list[str]):
	# 	for dep in path:
	# 		if dep in self.data:
	# 			del self.data[dep]
	# 	return super()._attempt_backtrack(ctx, gizmo, path)


	def _graceful_grab(self, path: list[Tuple[str, AbstractGadget]],
					   error: GrabError, ctx: AbstractGame, gizmo: str) -> Any:
		# clear cache as necessary based on path
		for target, gadget in path:
			if target in self.data:
				del self.data[target]
		return super()._graceful_grab(path, error, ctx, gizmo)


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



