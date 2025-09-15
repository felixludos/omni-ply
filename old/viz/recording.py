from typing import Any, Optional, Callable, List, Iterable, Iterator, Dict, Union, Tuple
from collections import OrderedDict
from omnibelt import colorize
from tabulate import tabulate
import logging, time
from ...core import Context as _Context, ToolKit, tool, AbstractGame, AbstractGadget, MissingGadget, SkipGadget
from ...core.gaggles import LoopyGaggle
from ...core.gangs import GangBase
from ...core.games import CacheGame, GameBase, GatedCache
from ...core.graces import GracefulGaggle
from ...core import Gate as _Gate
from ..gaps import Mechanism as _Mechanism

from .util import report_time, SPECIAL_CHARACTER

# from ..mechanisms import MechanismBase, Mechanism as _Mechanism



class AbstractRecorder:
	def relabel(self, external: str, internal: str, typ: str = ''):
		raise NotImplementedError
	
	def attempt(self, gizmo: str, gadget: 'AbstractGadget'):
		raise NotImplementedError

	def cached(self, gizmo: str, value: Any):
		raise NotImplementedError

	def success(self, gizmo: str, gadget: 'AbstractGadget', value: Any):
		raise NotImplementedError

	def failure(self, gizmo: str, gadget: 'AbstractGadget', error: Exception):
		raise NotImplementedError

	def missing(self, gizmo: str):
		raise NotImplementedError

	def report(self, owner: 'AbstractRecordable', **kwargs):
		raise NotImplementedError



class AbstractRecordable:
	def record(self, record: AbstractRecorder = None):
		raise NotImplementedError

	def report(self):
		raise NotImplementedError

	def reset(self):
		raise NotImplementedError



class RecorderBase(AbstractRecorder):
	def __init__(self):
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

	def report(self, owner: 'AbstractRecordable', **kwargs):
		yield from self._log



class RecordableBase(AbstractRecordable):
	_active_recording = None
	_Recorder = RecorderBase


	def record(self, record: RecorderBase = None):
		if record is None:
			record = self._Recorder()
		self._active_recording = record
		return self


	def report(self, **kwargs):
		return self._active_recording.report(self, **kwargs)


	def reset(self):
		self._active_recording = None
		return self


logger = logging.getLogger('omniply.apps.viz.recording')

# class RecordingGaggle(LoopyGaggle, RecordableBase):
# 	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
# 		failures = OrderedDict()
# 		itr = self._grabber_stack.setdefault(gizmo, self._gadgets(gizmo))
# 		for gadget in itr:
# 			try:
# 				if self._active_recording:
# 					self._active_recording.attempt(gizmo, gadget)
# 				out = gadget.grab_from(ctx, gizmo)
# 			except self._GadgetFailure as e:
# 				if self._active_recording:
# 					self._active_recording.failure(gizmo, gadget, e)
# 				failures[e] = gadget
# 			except:
# 				logger.debug(f'{gadget!r} failed while trying to produce {gizmo!r}')
# 				raise
# 			else:
# 				if self._active_recording:
# 					self._active_recording.success(gizmo, gadget, out)
# 				if gizmo in self._grabber_stack:
# 					self._grabber_stack.pop(gizmo)
# 				return out
# 		if self._active_recording: # recent change
# 			self._active_recording.missing(gizmo)
# 		if gizmo in self._grabber_stack:
# 			self._grabber_stack.pop(gizmo)
# 		if failures:
# 			raise self._AssemblyFailedError(failures)
# 		raise self._MissingGadgetError(gizmo)



class RecordingGaggle(GracefulGaggle, RecordableBase):
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


class RecordingCached(CacheGame, RecordableBase):
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

from ...core.op import CachableMechanism, MutableGaggle, AbstractGang

class _Mechanism(CachableMechanism, MutableGaggle, AbstractGang):
	def __init__(self, *gadgets: AbstractGadget, **kwargs):
		"""
		Initializes a new instance of the Gang class.

		This method initializes the superclass with the provided arguments and includes the provided gadgets in the gang.

		Args:
			gadgets (AbstractGadget): The gadgets to be included in the gang.
			kwargs: Arbitrary keyword arguments.
		"""
		super().__init__(**kwargs)
		self.extend(gadgets)

	def __getitem__(self, item):
		"""
		Returns the grabbed item from the context.

		Args:
			item: The item to be grabbed from the context.

		Returns:
			Any: The grabbed item from the context.
		"""
		return self.grab(item)



class Mechanism(_Mechanism, RecordingGaggle):
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


# class Mechanism(_Mechanism, RecordingMechanism):
# 	pass


class EventRecorder(RecorderBase):
	class _EventNode(ToolKit):
		_no_value = object()

		def __init__(self, gizmo=None, gadget=None, outcome=None, value=_no_value, error=None,
					 internal=None, external=None, router=None, start=None, end=None):
			super().__init__()
			self.gizmo = gizmo
			self.gadget = gadget
			self.outcome = outcome
			self.value = value
			self.error = error
			self.internal = internal
			self.external = external
			self.router = router
			self.followup = None
			self.children = []
			self.parent = None
			self.origin = None
			self.start = start
			self.end = end
			self.structure = None

		@property
		def duration(self):
			if self.start is not None and self.end is not None:
				return self.end - self.start

		# region getters
		@tool('gizmo')
		def get_gizmo(self):
			return self.gizmo
		@tool('gadget')
		def get_gadget(self):
			return self.gadget
		@tool('outcome')
		def get_outcome(self):
			return self.outcome
		@tool('value')
		def get_value(self):
			return self.value
		@tool('internal')
		def get_internal(self):
			return self.internal
		@tool('external')
		def get_external(self):
			return self.external
		@tool('router')
		def get_router(self):
			return self.router
		@tool('has_value')
		def has_value(self):
			return self.value is not self._no_value
		@tool('error')
		def get_error(self):
			return self.error
		@tool('followup')
		def get_followup(self):
			return self.followup
		@tool('children')
		def get_children(self):
			return self.children
		@tool('start')
		def get_start(self):
			return self.start
		@tool('end')
		def get_end(self):
			return self.end
		@tool('duration')
		def get_duration(self):
			return self.duration
		@tool('parent')
		def get_parent(self):
			return self.parent
		@tool('origin')
		def get_origin(self):
			return self.origin
		@tool('structure_prefix')
		def get_structure(self):
			return self.structure
		# endregion

		def __repr__(self):
			return f"Node({self.gizmo})"

	@classmethod
	def process_log(cls, log: List[tuple]) -> List[_EventNode]:
		root_nodes = []
		stack = []

		for event_type, *event in log:

			if event_type == 'relabel':
				external, internal, typ, ts = event
				if typ == 'external':
					node = cls._EventNode(gizmo=internal, external=external, start=ts)
					assert stack and stack[-1].gizmo == external, f'Attempted gizmo {external!r} does not match relabel {stack[-1].gizmo!r}'
					stack[-1].router = node
					node.origin = stack[-1]
				elif typ == 'internal':
					node = cls._EventNode(gizmo=external, internal=internal, start=ts)
					parent = stack[-1].children if stack else root_nodes
					if stack: node.parent = stack[-1]
					parent.append(node)
				else:
					raise ValueError(f'Invalid relabel type: {typ}')
				stack.append(node)

			elif event_type == 'attempt':
				gizmo, gadget, ts = event
				node = None
				while stack and (stack[-1].gizmo == gizmo or stack[-1].outcome == 'failure'):
					node = stack.pop()
					if node.gizmo == gizmo: break
				if node is None:
					node = cls._EventNode(gizmo=gizmo, gadget=gadget, start=ts)
					parent = stack[-1].children if stack else root_nodes
					if stack: node.parent = stack[-1]
					parent.append(node)
				elif node.outcome == 'failure': # past failure
					followup = cls._EventNode(gizmo=gizmo, gadget=gadget, start=ts)
					node.followup = followup
					followup.origin = node
					node = followup
				elif node.internal is not None or node.external is not None: # waiting relabel
					assert node.gadget is None, f'Attempted gizmo {gizmo!r} already has a gadget {node.gadget!r}'
					node.gadget = gadget
					# node.start = ts # NOTE: overwrites start time from relabel event
				else: # loopy
					stack.append(node)
					node = cls._EventNode(gizmo=gizmo, gadget=gadget, start=ts)
				stack.append(node)

			elif event_type == 'cached':
				gizmo, value, ts = event
				node = None
				while stack and (stack[-1].gizmo == gizmo or stack[-1].outcome == 'failure'):
					node = stack.pop()
					if node.gizmo == gizmo: break
				if node is None:
					node = cls._EventNode(gizmo=gizmo, outcome='cached', value=value, start=ts)
					parent = stack[-1].children if stack else root_nodes
					if stack: node.parent = stack[-1]
					parent.append(node)
				elif node.outcome is None: # open attempt or relabel
					node.outcome = 'cached'
					node.end = ts
					node.value = value
				elif node.outcome == 'failure':
					node.followup = cls._EventNode(gizmo=gizmo, outcome='cached', value=value, start=ts)
				else:
					raise ValueError('confused')
				for n in stack: n.outcome = None

			elif event_type == 'success':
				gizmo, gadget, value, ts = event
				while stack:
					node = stack.pop()
					if node.gizmo == gizmo:
						break
					# TODO: fix recording to handle graceful gaggles
					#  (uncomment to reveal unit tests with issues)
					# assert node.outcome == 'failure'
				else:
					raise ValueError(f'No active attempt for success event: {event}')
				node.outcome = 'success'
				node.value = value
				node.end = ts
				for n in stack: n.outcome = None

			elif event_type == 'failure':
				gizmo, gadget, error, ts = event
				while stack:
					node = stack.pop()
					node.outcome = 'failure'
					if node.gizmo == gizmo:
						node.error = error
						node.end = ts
						for n in stack: n.outcome = 'failure'
						stack.append(node)
						break
				else:
					node = cls._EventNode(gizmo=gizmo, outcome='failure', error=error, start=ts, end=ts)
					parent = stack[-1].children if stack else root_nodes
					if stack: node.parent = stack[-1]
					parent.append(node)
					stack.append(node)

		return root_nodes


	@classmethod
	def view_tree_structure(cls, node: _EventNode, prefix='', is_first=True, is_last=True, *,
							width=4, printer: Callable[[_EventNode], str] = None):
		if printer is None:
			printer = lambda node: node.gizmo
		assert width >= 2, 'width must be at least 2'
		# Determine the connector
		# is_last = is_last or node.followup is not None
		if is_first:
			connector = ''
		elif node.followup is not None:
			connector = '│' + ' ' * (width - 2) + ' '
		elif is_last:
			connector = '└' + '─' * (width - 2) + ' '
		else:
			connector = '├' + '─' * (width - 2) + ' '
		# Print the attempt

		yield prefix + connector + printer(node)

		# Prepare the new prefix for child nodes
		if is_first:
			child_prefix = prefix
		elif is_last:
			child_prefix = prefix + ' ' * width
		else:
			child_prefix = prefix + '│' + ' ' * (width - 1)

		# Print each child
		count = len(node.children)
		for i, child in enumerate(node.children):
			yield from cls.view_tree_structure(child, child_prefix, False, (i == count - 1),
										   width=width, printer=printer)

		if node.followup:
			yield from cls.view_tree_structure(node.followup, prefix, is_first, False,
										   width=width, printer=printer)

		if node.router:
			yield from cls.view_tree_structure(node.router, child_prefix, False, True,
										   width=width, printer=printer)


	class _EventViewer(ToolKit):
		@tool('function')
		def gadget_function(self, gadget):
			fn = getattr(gadget, '_fn', None)
			return fn

		@tool('module')
		def gadget_module(self, function):
			if function is not None:
				return getattr(function, '__module__', None)

		@tool('shortname')
		def gadget_shortname(self, function):
			if function is not None:
				return getattr(function, '__name__', None)

		@tool('qualname')
		def gadget_qualname(self, function):
			if function is not None:
				return getattr(function, '__qualname__', None)

		@tool('name')
		def gadget_name(self, qualname, shortname):
			return qualname or shortname

		@tool('filepath')
		def gadget_filepath(self, module):
			return getattr(module, '__file__', None)


		@tool('title')
		def render_title(self, structure_prefix, gizmo, outcome, internal, external, gadget):
			colors = {'success': 'green', 'failure': 'red', None: 'red',
					  'cached': 'blue', 'missing': 'red'}
			name = colorize(gizmo, color=colors.get(outcome, "yellow"))
			alt = None
			if external is not None:
				name = f'({name})'
			elif internal is not None:
				alt = internal
			ungapper = getattr(gadget, 'gap_invert', None)
			if ungapper is not None:
				alt = ungapper(alt or gizmo) or alt
			if alt is not None:
				# use left arrow characters like: ←
				# name = f'{name} ({alt})'
				# name = f'({alt}) → {name}'
				name = f'{name} (← {alt})'
			return f'{structure_prefix}{name}'

		@tool('safe_title')
		def render_safe_title(self, title):
			'''this is useful as tabulate removes padding'''
			return title.replace(' ', SPECIAL_CHARACTER)

		@tool('pretty_name')
		def render_pretty_name(self, name, gadget):
			if name is not None:
				terms = name.split('.')
				return '.'.join([*terms[:-1], colorize(terms[-1], color='magenta')])
			if gadget is not None:
				return self._cap_string(str(gadget), length=30, first_line=True)
			return ''

		@tool('status')
		def render_status(self, duration, external=None):
			return report_time(duration) if external is None and duration is not None and duration > 0 else ''

		def _cap_string(self, raw, length=50, first_line=False):
			assert length > 3, f'length must be at least 3: {length}'
			full = raw.split('\n', 1)[0] if first_line else raw.replace('\n', '\\n')
			full = full.replace('\t', '\\t')
			return full[:length-3] + '...' if len(full) > length else full

		@tool('info')
		def render_info(self, has_value, value, error, external=None):
			if not has_value:
				if error is not None:
					msg = f'{error.__class__.__name__}: {error}' if isinstance(error, Exception) else f'Error: {error}'
					msg = self._cap_string(msg)
					return colorize(msg, color='red')
				return ''
			if external is not None:
				return ''
			full = self._cap_string(str(value))
			return f'"{full}"' if isinstance(value, str) else full


	def report(self, owner: AbstractRecordable, *, columns: Iterable[str] = None, width: int = 4,
			   ret_ctx: bool = False,
			   workers: Optional[List[AbstractGadget]] = ()):
		workers = list(workers)
		if self._EventViewer is not None:
			workers.append(self._EventViewer())

		log = self._log
		roots = self.process_log(self._log)

		all_nodes = []
		def _capture_node(node):
			all_nodes.append(node)
			return ''

		for root in roots:
			for line in self.view_tree_structure(root, width=width, printer=_capture_node):
				all_nodes[-1].structure = line

		rows = [_Context(*workers, node) for node in all_nodes]

		if ret_ctx:
			return rows
		if columns is None:
			columns = ['safe_title', # used to keep leading whitespace of structure_prefix
					   'status', 'pretty_name', 'info']

		table = [[row.grab(column) for column in columns] for row in rows]

		# widths = [None] * len(columns)
		# for row in table:
		# 	for i, cell in enumerate(row):
		# 		if widths[i] is None or len(cell) > widths[i]:
		# 			widths[i] = wcswidth(cell)
		# lines = []
		# for row in table:
		# 	line = '  '.join(cell.ljust(width) for cell, width in zip(row, widths))
		# 	lines.append(line)
		# return '\n'.join(lines)

		# tabulate with minimal formatting
		return tabulate(table, tablefmt='plain').replace(SPECIAL_CHARACTER, ' ')


from ...core.errors import AbstractGadgetError, GrabError
from ...core.op import ConsistentGame, RollingGame, GracefulCache, MutableGaggle, GeneticGaggle

class _Context(GatedCache, ConsistentGame, RollingGame, GracefulCache, MutableGaggle, GeneticGaggle, AbstractGame):

	def __init__(self, *gadgets: AbstractGadget, **kwargs):
		"""
		Initializes a new instance of the Context class.

		This method initializes the superclass with the provided arguments and includes the provided gadgets in the context.

		Args:
			gadgets (AbstractGadget): The gadgets to be included in the context.
			kwargs: Arbitrary keyword arguments.
		"""
		super().__init__(**kwargs)
		self.extend(gadgets)


	def gabel(self, *args, **kwargs):
		'''effectively a shallow copy, excluding the cache'''
		new = self.__class__(*args, **kwargs)
		new.extend(self.vendors())
		return new


	def get(self, key: str, default: Any = None) -> Any:
		return self.grab(key, default=default)


	def __getitem__(self, item):
		"""
		Returns the grabbed item from the context.

		Args:
			item: The item to be grabbed from the context.

		Returns:
			Any: The grabbed item from the context.
		"""
		return self.grab(item)



class Context(_Context, RecordingCached, GameBase, RecordingGaggle):
	_Recorder = EventRecorder


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







