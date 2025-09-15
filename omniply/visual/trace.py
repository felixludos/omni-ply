from typing import Any, Optional, Callable, List, Iterable, Iterator, Dict, Union, Tuple
from omnibelt import colorize
from tabulate import tabulate
from ..core import Context, ToolKit, tool, AbstractGame, AbstractGadget
from ..core.recording import RecorderBase, AbstractRecordable

from .util import report_time, SPECIAL_CHARACTER



class TraceRecorder(RecorderBase):
	class _TraceNode(ToolKit):
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
	def process_log(cls, log: List[tuple]) -> List[_TraceNode]:
		root_nodes = []
		stack = []

		for event_type, *event in log:

			if event_type == 'relabel':
				external, internal, typ, ts = event
				if typ == 'external':
					node = cls._TraceNode(gizmo=internal, external=external, start=ts)
					assert stack and stack[-1].gizmo == external, f'Attempted gizmo {external!r} does not match relabel {stack[-1].gizmo!r}'
					stack[-1].router = node
					node.origin = stack[-1]
				elif typ == 'internal':
					node = cls._TraceNode(gizmo=external, internal=internal, start=ts)
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
					node = cls._TraceNode(gizmo=gizmo, gadget=gadget, start=ts)
					parent = stack[-1].children if stack else root_nodes
					if stack: node.parent = stack[-1]
					parent.append(node)
				elif node.outcome == 'failure': # past failure
					followup = cls._TraceNode(gizmo=gizmo, gadget=gadget, start=ts)
					node.followup = followup
					followup.origin = node
					node = followup
				elif node.internal is not None or node.external is not None: # waiting relabel
					assert node.gadget is None, f'Attempted gizmo {gizmo!r} already has a gadget {node.gadget!r}'
					node.gadget = gadget
					# node.start = ts # NOTE: overwrites start time from relabel event
				else: # loopy
					stack.append(node)
					node = cls._TraceNode(gizmo=gizmo, gadget=gadget, start=ts)
				stack.append(node)

			elif event_type == 'cached':
				gizmo, value, ts = event
				node = None
				while stack and (stack[-1].gizmo == gizmo or stack[-1].outcome == 'failure'):
					node = stack.pop()
					if node.gizmo == gizmo: break
				if node is None:
					node = cls._TraceNode(gizmo=gizmo, outcome='cached', value=value, start=ts)
					parent = stack[-1].children if stack else root_nodes
					if stack: node.parent = stack[-1]
					parent.append(node)
				elif node.outcome is None: # open attempt or relabel
					node.outcome = 'cached'
					node.end = ts
					node.value = value
				elif node.outcome == 'failure':
					node.followup = cls._TraceNode(gizmo=gizmo, outcome='cached', value=value, start=ts)
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
					node = cls._TraceNode(gizmo=gizmo, outcome='failure', error=error, start=ts, end=ts)
					parent = stack[-1].children if stack else root_nodes
					if stack: node.parent = stack[-1]
					parent.append(node)
					stack.append(node)

		return root_nodes


	@classmethod
	def view_tree_structure(cls, node: _TraceNode, prefix='', is_first=True, is_last=True, *,
							width=4, printer: Callable[[_TraceNode], str] = None):
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

		rows = [Context(*workers, node) for node in all_nodes]

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





