from typing import Any, Optional, Callable, List, Iterable, Iterator, Dict, Union, Tuple
import logging, time
from omnibelt import colorize
from tabulate import tabulate
from .errors import SkipGadget, AbstractGadgetError, GrabError
from .abstract import AbstractRecordable, AbstractRecorder
from .graces import GracefulGaggle
from .gangs import CachableMechanism, GangBase
from .games import CacheGame, GatedCache, GameBase, AbstractGame



class RecorderBase(AbstractRecorder):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._log = []

	def relabel(self, external: str, internal: str, typ: str = ''):
		self._log.append(('relabel', external, internal, typ, time.time()))

	def attempt(self, gizmo: str, gadget: 'AbstractGadget'):
		self._log.append(('attempt', gizmo, gadget, time.time()))

	def cached(self, gizmo: str, value: Any):
		self._log.append(('cached', gizmo, value, time.time()))

	def success(self, gizmo: str, gadget: 'AbstractGadget', value: Any):
		self._log.append(('success', gizmo, gadget, value, time.time()))

	def failure(self, gizmo: str, gadget: 'AbstractGadget', error: Optional[Exception]):
		self._log.append(('failure', gizmo, gadget, error, time.time()))

	def missing(self, gizmo: str):
		self._log.append(('missing', gizmo, time.time()))

	def prepare(self, owner: 'AbstractRecordable', **kwargs) -> 'Self':
		return self

	def report(self, owner: 'AbstractRecordable', **kwargs):
		yield from self._log



class RecordableBase(AbstractRecordable):
	_active_recording: Optional[AbstractRecorder] = None


	def record(self, recorder: AbstractRecorder, **kwargs):
		self._active_recording = recorder.prepare(self, **kwargs) if isinstance(recorder, AbstractRecorder) \
			else recorder
		return self


	def report(self, **kwargs):
		return self._active_recording.report(self, **kwargs)


	# def reset(self):
	# 	self._active_recording = None
	# 	return self



class RecordableGaggle(GracefulGaggle, RecordableBase):
	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
		if len(self._grab_trace) == 0:
			self._grab_query = gizmo
			self._grab_tree.clear()
			self._grabber_stack.clear()
		self._grab_trace.append(gizmo)

		itr = self._grabber_stack.setdefault(gizmo, self._gadgets(gizmo))

		try:
			gadget = next(itr)
		except self._MissingGadgetError:
			if self._active_recording: # recent change
				self._active_recording.missing(gizmo)
			self._grab_trace.pop()  # failed to grab the gizmo, so pop it from the trace
			raise
		except StopIteration:
			if self._active_recording: # recent change
				self._active_recording.missing(gizmo)
			self._grab_trace.pop()  # failed to grab the gizmo, so pop it from the trace
			raise self._MissingGadgetError(gizmo)

		if self._active_recording:
			self._active_recording.attempt(gizmo, gadget)

		try:
			result = gadget.grab_from(ctx, gizmo)

		except SkipGadget:
			result = self.grab_from(ctx, gizmo)

		except self._GadgetFailure as error:

			if self._active_recording:
				self._active_recording.failure(gizmo, gadget, error)

			# attempt backtracking
			grace_path = self._ask_for_grace(ctx, error, gadget, tuple(self._grab_trace))
			if grace_path is None:
				self._grab_trace.pop()  # failed to grab the gizmo, so pop it from the trace
				raise error
			result = self._graceful_grab(grace_path, error, ctx, gizmo)

		if self._active_recording:
			self._active_recording.success(gizmo, gadget, result)
		# except:
		# 	logger.debug(f'{gadget!r} failed while trying to produce {gizmo!r}')
		# 	raise

		assert self._grab_trace[-1] == gizmo, (f'Expected {gizmo!r} to be the last in the trace, '
											   f'but got {self._grab_trace[-1]!r}')
		self._grab_trace.pop()  # completed gizmo, so pop it from the trace
		self._grab_tree.setdefault(tuple(self._grab_trace), []).append((gizmo, gadget))  # update grab tree

		# if len(self._grab_trace) == 0:
		# 	self._grab_tree.clear()
		# 	self._grabber_stack.clear()
		return result



class RecordableGame(GameBase, RecordableBase):
	def _grab_from_fallback(self, error: Exception, ctx: Optional['AbstractGame'], gizmo: str) -> Any:
		"""
		Handles a GadgetFailure when trying to grab a gizmo from the context.

		Args:
			error (Exception): The exception that occurred during the grab operation.
			ctx (Optional[AbstractGame]): The context from which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The result of the fallback operation.

		Raises:
			_GrabError: If the error is a GrabError or if the context is None or self.
			error: If the error is not a GrabError.
		"""
		if isinstance(error, AbstractGadgetError):
			if isinstance(error, GrabError) or ctx is None or ctx is self:
				if self._active_recording:
					self._active_recording.failure(gizmo, None, error)
				raise self._GrabError(gizmo, error) from error
			else:
				return ctx.grab(gizmo)
		raise error from error



class RecordableCached(CacheGame, RecordableGame):
	def grab_from(self, ctx: Optional['AbstractGame'], gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the context.

		Args:
			ctx (Optional[AbstractGame]): The context from which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		if gizmo in self.data:
			out = self.data[gizmo]
			if self._active_recording:
				self._active_recording.cached(gizmo, out)
			return out
		val = self._cache_miss(ctx, gizmo)
		self[gizmo] = val  # cache packaged val
		return val



class RecordableMechanism(CachableMechanism, RecordableGaggle):
	def _grab(self, gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the gate. If the gizmo is not found in the gate's cache, it checks the cache using
		the external gizmo name. If it still can't be found in any cache, it grabs it from the gate's gadgets.

		Args:
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		if len(self._gang_stack):
			# check cache (if one exists)
			ext = self.gizmo_to(gizmo)
			for parent in reversed(self._gang_stack):
				if isinstance(parent, GatedCache):
					try:
						out = parent.check_gate_cache(self, gizmo)
					except self._GateCacheMiss:
						pass
					else:
						if self._active_recording:
							self._active_recording.cached(gizmo, out)
						return out
				# if it can't be found in my cache, check the cache using the external gizmo name
				if ext is not None and isinstance(parent, CacheGame) and parent.is_cached(ext):
					return parent.grab(ext)

		# if it can't be found in any cache, grab it from my gadgets
		out = super(GangBase, self).grab_from(self, gizmo)

		# update my cache
		if len(self._gang_stack):
			for parent in reversed(self._gang_stack):
				if isinstance(parent, GatedCache):
					parent.update_gate_cache(self, gizmo, out)
					break

		return out


	def grab_from(self, ctx: 'AbstractRecordable', gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the context.

		Args:
			ctx (Optional[AbstractGame]): The context from which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		if ctx is None or ctx is self: # internal grab
			internal = self._internal_map.get(gizmo, gizmo)
			if self._active_recording:
				self._active_recording.relabel(internal, gizmo, 'internal')
			try:
				out = self._grab(internal)
			except (self._GadgetFailure, self._MissingGadgetError) as e:
				# default to parent/s
				if self._insulated and gizmo not in self._internal_map:
					if self._active_recording:
						self._active_recording.failure(gizmo, None, e)
					raise
				for parent in reversed(self._gang_stack):
					try:
						out = parent.grab(internal)
					except self._GadgetFailure:
						pass
					else:
						break
				else:
					if self._active_recording:
						self._active_recording.failure(gizmo, None, e)
					raise

		else: # was called from an external context
			self._gang_stack.append(ctx)
			rec = getattr(ctx, '_active_recording', None)
			if rec is not None:
				self._active_recording = rec
			prev = gizmo
			gizmo = self._reverse_external_map.get(gizmo, gizmo)
			if self._active_recording:
				self._active_recording.relabel(prev, gizmo, 'external')
			out = self._grab(gizmo)

		if len(self._gang_stack) and ctx is self._gang_stack[-1]:
			if (len(self._gang_stack) == 1
					and self._active_recording is getattr(self._gang_stack[-1], '_active_recording', None)):
				self._active_recording = None
			self._gang_stack.pop()

		return out






