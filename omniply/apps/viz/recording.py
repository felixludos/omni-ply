from typing import Any, Optional, Callable, List, Iterable, Iterator, Dict, Union, Tuple
from collections import OrderedDict
from omnibelt import colorize
from tabulate import tabulate
import logging, time
from ...core import Context as _Context, ToolKit, tool, AbstractGadget, MissingGadget
from ...core.gaggles import LoopyGaggle
from ...core.games import CacheGame, GameBase, GatedCache

from .util import report_time, SPECIAL_CHARACTER

from ..mechanisms import MechanismBase, Mechanism as _Mechanism



class AbstractRecorder:
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



class AbstractRecordable:
	def record(self, record: AbstractRecorder = None):
		raise NotImplementedError

	def report(self):
		raise NotImplementedError

	def reset(self):
		raise NotImplementedError

	# def record_relabel(self, external: str, internal: str):
	# 	raise NotImplementedError



class RecorderBase:
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

	def failure(self, gizmo: str, gadget: 'AbstractGadget', error: Exception):
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


	# def record_relabel(self, external: str, internal: str):
	# 	if self._active_recording:
	# 		self._active_recording.relabel(external, internal)


	def report(self, **kwargs):
		return self._active_recording.report(self, **kwargs)


	def reset(self):
		self._active_recording = None
		return self


logger = logging.getLogger('omniply.apps.viz.recording')

class RecordingGaggle(LoopyGaggle, RecordableBase):
	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
		failures = OrderedDict()
		itr = self._grabber_stack.setdefault(gizmo, self._gadgets(gizmo))
		try:
			for gadget in itr:
				try:
					if self._active_recording:
						self._active_recording.attempt(gizmo, gadget)
					out = gadget.grab_from(ctx, gizmo)
				except self._GadgetFailure as e:
					if self._active_recording:
						self._active_recording.failure(gizmo, gadget, e)
					failures[e] = gadget
				except:
					logger.debug(f'{gadget!r} failed while trying to produce {gizmo!r}')
					raise
				else:
					if self._active_recording:
						self._active_recording.success(gizmo, gadget, out)
					if gizmo in self._grabber_stack:
						self._grabber_stack.pop(gizmo)
					return out
		except self._MissingGadgetError:
			# if self._active_recording:
			# 	self._active_recording.missing(gizmo)
			raise
		if self._active_recording: # recent change
			self._active_recording.missing(gizmo)
		if gizmo in self._grabber_stack:
			self._grabber_stack.pop(gizmo)
		if failures:
			raise self._AssemblyFailedError(failures)
		raise self._MissingGadgetError(gizmo)



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


class RecordingMechanism(MechanismBase, RecordingGaggle):
	def _grab(self, gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the gate. If the gizmo is not found in the gate's cache, it checks the cache using
		the external gizmo name. If it still can't be found in any cache, it grabs it from the gate's gadgets.

		Args:
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		if len(self._game_stack):
			# check cache (if one exists)
			for parent in reversed(self._game_stack):
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
			ext = self._select_map.get(gizmo)
			if ext is not None:
				for parent in reversed(self._game_stack):
					if isinstance(parent, GatedCache) and parent.is_cached(ext):
						return parent.grab(ext)

		# if it can't be found in any cache, grab it from my gadgets
		out = super(MechanismBase, self).grab_from(self, gizmo)

		# update my cache
		if len(self._game_stack):
			for parent in reversed(self._game_stack):
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
			fixed = self._apply_map.get(gizmo, gizmo)
			if self._active_recording:
				self._active_recording.relabel(fixed, gizmo, 'internal')
			try:
				out = self._grab(fixed)
			except self._MissingGadgetError: # important change
				# default to parent/s
				if self._insulate_in and gizmo not in self._apply_map:
					raise
				for parent in reversed(self._game_stack):
					try:
						out = parent.grab(fixed)
					except self._GadgetFailure:
						pass
					else:
						break
				else:
					if self._active_recording:
						self._active_recording.missing(gizmo)
					raise

		else: # grab from external context
			self._game_stack.append(ctx)
			rec = getattr(ctx, '_active_recording', None)
			if rec is not None:
				self._active_recording = rec
			prev = gizmo
			gizmo = self._reverse_select_map.get(gizmo, gizmo)
			if self._active_recording:
				self._active_recording.relabel(prev, gizmo, 'external')
			out = self._grab(gizmo)


		if len(self._game_stack) and ctx is self._game_stack[-1]:
			if (len(self._game_stack) == 1
					and self._active_recording is getattr(self._game_stack[-1], '_active_recording', None)):
				self._active_recording = None
			self._game_stack.pop()

		return out


class Mechanism(_Mechanism, RecordingMechanism):
	pass


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
				# _, gizmo, gadget = event
				gizmo, gadget, ts = event
				if stack and stack[-1].gizmo == gizmo and (stack[-1].internal is not None or stack[-1].external is not None):
					assert stack[-1].gadget is None, f'Attempted gizmo {gizmo!r} already has a gadget {stack[-1].gadget!r}'
					# assert stack[-1].gizmo == gizmo, f'Attempted gizmo {gizmo!r} does not match relabel {stack[-1].gizmo!r}'
					stack[-1].gadget = gadget
					# stack[-1].start = ts # NOTE: overwrites start time from relabel event
				else:
					node = cls._EventNode(gizmo=gizmo, gadget=gadget, start=ts)
					parent = stack[-1].children if stack else root_nodes
					if len(parent) and parent[-1].gizmo == gizmo and parent[-1].outcome == 'failure':
						assert parent[-1].followup is None
						parent[-1].followup = node
						node.origin = parent[-1]
					else:
						if stack: node.parent = stack[-1]
						parent.append(node)
					stack.append(node)

			# elif event_type == 'relabel':
			# 	external, internal, typ, ts = event
			# 	if typ == 'internal':
			# 		node = cls._EventNode(gizmo=external, internal=internal, start=ts)
			# 		parent = stack[-1].children if stack else root_nodes
			# 		if stack: node.parent = stack[-1]
			# 		parent.append(node)
			# 		stack.append(node)
			# 	elif typ == 'external':
			# 		assert len(stack) > 0, f'No active attempt for relabel event: {event}'
			# 		assert stack[-1].gizmo == external, f'Attempted gizmo {external!r} does not match relabel {stack[-1].gizmo!r}'
			# 		assert stack[-1].relabel is None, f'Attempted gizmo {external!r} already has a relabel {stack[-1].relabel!r}'
			# 		stack[-1].relabel = internal
			# 	else:
			# 		raise ValueError(f'Invalid relabel type: {typ}')

			elif event_type == 'cached':
				gizmo, value, ts = event
				if stack and stack[-1].gizmo == gizmo and stack[-1].outcome is None:
					# assert stack[-1].gizmo == gizmo, f'Attempted gizmo {gizmo!r} does not match relabel {stack[-1].gizmo!r}'
					stack[-1].outcome = 'cached'
					stack[-1].end = ts
					stack[-1].value = value
					stack.pop()
				else:
					node = cls._EventNode(gizmo=gizmo, outcome='cached', value=value, start=ts, end=ts)
					parent = stack[-1].children if stack else root_nodes
					if len(parent) and parent[-1].gizmo == gizmo and parent[-1].outcome == 'failure':
						assert parent[-1].followup is None
						parent[-1].followup = node
						node.origin = parent[-1]
					else:
						if stack: node.parent = stack[-1]
						parent.append(node)

			elif event_type == 'success':
				gizmo, gadget, value, ts = event
				assert len(stack) > 0, f'No active attempt for success event: {event}'
				node = stack.pop()
				# assert node.gizmo == gizmo and node.gadget == gadget # recent change
				node.outcome = 'success'
				node.value = value
				node.end = ts
			elif event_type == 'failure':
				gizmo, gadget, error, ts = event

				if isinstance(error, MissingGadget):
					node = cls._EventNode(gizmo=gizmo, outcome='missing', start=ts, end=ts, error=error)
					parent = stack[-1].children if stack else root_nodes
					if stack: node.parent = stack[-1]
					parent.append(node)
				else:
					assert len(stack) > 0, f'No active attempt for failure event: {event}'
					node = None
					while stack and (node is None or node.gizmo != gizmo):
						node = stack.pop()
					# assert node.gizmo == gizmo and (gadget is None or node.gadget == gadget)
					if node is not None and node.gizmo == gizmo:
						node.outcome = 'failure'
						node.error = error
						node.end = ts
			elif event_type == 'missing':
				# raise NotImplemented('not currently supported as all "missing" events should be recorded as a "failure"')
				gizmo, ts = event
				if stack and stack[-1].gizmo == gizmo and stack[-1].outcome is None:
					stack[-1].outcome = 'missing'
					stack[-1].end = ts
					stack[-1].error = 'missing'
					stack.pop()
				else:
					node = cls._EventNode(gizmo=gizmo, outcome='missing', start=ts, end=ts, error='missing')
					parent = stack[-1].children if stack else root_nodes
					if stack: node.parent = stack[-1]
					parent.append(node)
				# while len(stack) and stack[-1].outcome is None:
				# 	parent = stack.pop()
				# 	parent.outcome = 'failure'
				# 	parent.error = f'{gizmo!r} missing'
				# 	parent.end = ts

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



def test_recording():

	from ..gaps import tool, ToolKit
	from ...core import GadgetFailure, MissingGadget, GrabError

	class Tester(ToolKit):
		@tool('a')
		def f(self):
			return 10

		@tool('b')
		def g(self, a):
			return a + 10

		@tool('c')
		def h(self, b, d):
			return b - d

	@tool('b')
	def i():
		raise GadgetFailure

	ctx = Context(i, Tester(gap={'a': 'x'}))

	ctx['d'] = 5

	ctx.record()

	assert ctx.grab('c') == 15

	ctx.clear_cache()

	assert ctx.grab('x') == 10
	assert ctx.grab('b') == 20

	try:
		ctx.grab('c') # d is missing
	except GrabError:
		pass

	assert ctx.grab('x') == 10

	report = ctx.report(ret_ctx=True)

	print()

	pretty = ctx.report()
	print(pretty)
	print()


def test_loopy():
	from ...core import tool, ToolKit

	@tool('a')
	def i():
		return 5

	@tool('a')
	def j(a):
		return a - 1

	ctx = Context(j, i)

	ctx.record()

	assert ctx.grab('a') == 4

	report = ctx.report(ret_ctx=True)

	print()

	pretty = ctx.report()
	print(pretty)
	print()


def test_mech_recording():

	from ...core import tool, ToolKit
	from ...core import GadgetFailure, MissingGadget, GrabError

	class Tester(ToolKit):
		@tool('a')
		def f(self):
			return 10

		@tool('b')
		def g(self, a):
			return a + 4

		@tool('c')
		def h(self, a, b):
			return b - a

	src = Tester()
	mech = Mechanism(src, select={'c': 'd'}, apply={'b': 'a'})
	ctx = Context(src, mech)

	print()
	ctx.record()

	assert ctx.grab('c') == 4

	print(ctx.report())

	ctx.clear_cache()
	print()
	ctx.record()

	assert ctx.grab('d') == 0

	print(ctx.report())


def test_double_mech_recording():
	from ...core import tool, ToolKit
	from ..simple import DictGadget

	class Tester1(ToolKit):
		@tool('hidden')
		def f(self):
			return 5

		@tool('a')
		def g(self, x):
			return 50 - x

	class Tester2(ToolKit):
		@tool('b')
		def h(self):
			return 100

		@tool('c')
		def h(self, b):
			return b - 10

	mech1 = Mechanism(Tester1(), select={'a': 'y', 'hidden': 'b'}, apply={'x': 'b'})
	mech2 = Mechanism(Tester2(), select={'c': 'out'}, apply={'b': 'y'})
	ctx = Context(mech1, mech2)

	print()
	ctx.record()

	assert list(ctx.gizmos()) == ['b', 'y', 'out']

	assert ctx.grab('out') == 35

	print(ctx.report())

	ctx.clear_cache()
	print()
	# ctx.record()
	# assert ctx.grab('d') == 0
	# print(ctx.report())






