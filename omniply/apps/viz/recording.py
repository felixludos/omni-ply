from typing import Any, Optional, Callable, List, Iterable, Iterator, Dict, Union, Tuple
from collections import OrderedDict
from omnibelt import colorize
from tabulate import tabulate
import logging, time
from ...core import Context as _Context, ToolKit, tool, AbstractGadget
from ...core.gaggles import LoopyGaggle
from ...core.games import CacheGame, GameBase

from .util import report_time


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



class RecorderBase:
	def __init__(self):
		self._log = []

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
			if self._active_recording:
				self._active_recording.missing(gizmo)
			raise
		if self._active_recording:
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



class EventRecorder(RecorderBase):
	class _EventNode(ToolKit):
		_no_value = object()

		def __init__(self, gizmo=None, gadget=None, outcome=None, value=_no_value, error=None, start=None, end=None):
			super().__init__()
			self.gizmo = gizmo
			self.gadget = gadget
			self.outcome = outcome
			self.value = value
			self.error = error
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
			if event_type == 'attempt':
				# _, gizmo, gadget = event
				gizmo, gadget, ts = event
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

			elif event_type == 'cached':
				gizmo, value, ts = event
				node = cls._EventNode(gizmo=gizmo, outcome='cached', value=value, start=ts, end=ts)
				parent = stack[-1].children if stack else root_nodes
				if stack: node.parent = stack[-1]
				parent.append(node)

			elif event_type == 'success':
				gizmo, gadget, value, ts = event
				assert len(stack) > 0, f'No active attempt for success event: {event}'
				node = stack.pop()
				assert node.gizmo == gizmo and node.gadget == gadget
				node.outcome = 'success'
				node.value = value
				node.end = ts
			elif event_type == 'failure':
				gizmo, gadget, error, ts = event
				assert len(stack) > 0, f'No active attempt for failure event: {event}'
				node = stack.pop()
				assert node.gizmo == gizmo and node.gadget == gadget
				node.outcome = 'failure'
				node.error = error
				node.end = ts
			elif event_type == 'missing':
				gizmo, ts = event
				node = cls._EventNode(gizmo=gizmo, outcome='missing', start=ts, end=ts, error='missing')
				parent = stack[-1].children if stack else root_nodes
				if stack: node.parent = stack[-1]
				parent.append(node)
				while len(stack) and stack[-1].outcome is None:
					parent = stack.pop()
					parent.outcome = 'failure'
					parent.error = f'{gizmo!r} missing'
					parent.end = ts

		return root_nodes


	@classmethod
	def view_tree_structure(cls, node: _EventNode, prefix='', is_first=True, is_last=True, is_followup=False, *,
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
			yield from cls.view_tree_structure(node.followup, prefix, is_first, False, True,
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
		def render_title(self, structure_prefix, gizmo, outcome):
			colors = {'success': 'green', 'failure': 'red', 'cached': 'blue', 'missing': 'red'}
			return f'{structure_prefix}{colorize(gizmo, color=colors.get(outcome, "yellow"))}'

		@tool('pretty_name')
		def render_pretty_name(self, name):
			if name is not None:
				terms = name.split('.')
				return '.'.join([*terms[:-1], colorize(terms[-1], color='magenta')])
			return ''

		@tool('status')
		def render_status(self, duration):
			return report_time(duration) if duration is not None and duration > 0 else ''

		@tool('info')
		def render_info(self, has_value, value, error):
			if not has_value:
				if error is not None:
					msg = f'{error.__class__.__name__}: {error}' if isinstance(error, Exception) else f'Error: {error}'
					return colorize(msg, color='red')
				return ''
			full = str(value)
			full = full.replace('\n', '\\n').replace('\t', '\\t')
			raw = full[:47] + '...' if len(full) > 50 else full
			return f'"{raw}"' if isinstance(value, str) else raw


	def report(self, owner: AbstractRecordable, *, columns: Iterable[str] = None, width: int = 4,
			   ret_ctx: bool = False,
			   workers: Optional[List[AbstractGadget]] = ()):
		workers = list(workers)
		if self._EventViewer is not None:
			workers.append(self._EventViewer())

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
			columns = ['title', 'status', 'pretty_name', 'info']

		table = [[row.grab(column) for column in columns] for row in rows]

		# tabulate with minimal formatting
		return tabulate(table, tablefmt='plain')



class Context(_Context, RecordingCached, GameBase, RecordingGaggle):
	_Recorder = EventRecorder



def test_recording():

	from ...core import tool, ToolKit
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

	ctx = Context(i, Tester())

	ctx['d'] = 5

	ctx.record()

	assert ctx.grab('c') == 15

	ctx.clear_cache()

	assert ctx.grab('a') == 10
	assert ctx.grab('b') == 20

	try:
		ctx.grab('c') # d is missing
	except GrabError:
		pass

	assert ctx.grab('a') == 10

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









