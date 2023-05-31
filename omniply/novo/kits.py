from .imports import *

from .abstract import *
from .errors import *
from .tools import *



class Kit(AbstractToolKit, MyAbstractTool):
	_tools_table: Dict[str, List[AbstractTool]] # tools are kept in O-N order (reversed) for easy updates

	def __init__(self, *args, tools_table: Optional[Mapping] = None, **kwargs):
		if tools_table is None:
			tools_table = {}
		super().__init__(*args, **kwargs)
		self._tools_table = tools_table


	def gizmos(self) -> Iterator[str]:
		yield from self._tools_table.keys()


	def produces_gizmo(self, gizmo: str) -> bool:
		return gizmo in self._tools_table


	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractTool]:
		if gizmo is None:
			yield from filter_duplicates(chain.from_iterable(map(reversed, self._tools_table.values())))
		else:
			if gizmo not in self._tools_table:
				raise self._MissingGizmoError(gizmo)
			yield from reversed(self._tools_table[gizmo])


	_AssemblyFailedError = AssemblyFailedError
	def _get_from(self, ctx: 'AbstractContext', gizmo: str) -> Any:
		failures = []
		for tool in self.vendors(gizmo):
			try:
				return tool.get_from(ctx, gizmo)
			except ToolFailedError as e:
				failures.append((tool, e))
			except:
				prt.debug(f'{tool!r} failed while trying to produce: {gizmo!r}')
				raise
		if failures:
			raise self._AssemblyFailedError(gizmo, failures)
		raise self._ToolFailedError(gizmo)



class LoopyKit(Kit):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._get_from_status: Optional[Dict[str, Iterator[AbstractTool]]] = {}


	def _get_from(self, ctx: 'AbstractContext', gizmo: str) -> Any:
		failures = []
		itr = self._get_from_status.setdefault(gizmo, self.vendors(gizmo))
		# should be the same as Kit, except the iterators are cached until the gizmo is produced
		for tool in itr:
			try:
				out = tool.get_from(ctx, gizmo)
			except ToolFailedError as e:
				failures.append((tool, e))
			except:
				prt.debug(f'{tool!r} failed while trying to produce: {gizmo!r}')
				raise
			else:
				if gizmo in self._get_from_status:
					self._get_from_status.pop(gizmo)
				return out
		if failures:
			raise self._AssemblyFailedError(gizmo, failures)
		raise self._ToolFailedError(gizmo)



class MutableKit(Kit):
	def include(self, *tools: AbstractTool) -> 'MutableKit': # TODO: return Self
		'''adds given tools in reverse order'''
		return self.extend(tools)
		
		
	def extend(self, tools: Iterable[AbstractTool]) -> 'MutableKit':
		new = {}
		for tool in tools:
			for gizmo in tool.gizmos():
				new.setdefault(gizmo, []).append(tool)
		for gizmo, tools in new.items():
			if gizmo in self._tools_table:
				for tool in tools:
					if tool in self._tools_table[gizmo]:
						self._tools_table[gizmo].remove(tool)
			self._tools_table.setdefault(gizmo, []).extend(reversed(tools))
		return self


	def exclude(self, *tools: AbstractTool) -> 'MutableKit':
		'''removes the given tools, if they are found'''
		for tool in tools:
			for gizmo in tool.gizmos():
				if gizmo in self._tools_table and tool in self._tools_table[gizmo]:
					self._tools_table[gizmo].remove(tool)
		return self
	


class CraftyKit(Kit, InheritableCrafty):
	def _process_crafts(self):
		# avoid duplicate keys (if you overwrite a method, only the last one will be used)
		items = OrderedDict()
		for src, key, craft in self._emit_all_craft_items(): # N-O
			if key not in items:
				items[key] = craft
			
		# convert crafts to skills and add in N-O order
		table = {}
		for key, craft in items.items(): # N-O
			for gizmo in craft.gizmos():
				table.setdefault(gizmo, []).append(craft.as_skill(self))
			
		# add N-O skills in reverse order for O-N _tools_table
		for gizmo, tools in reversed(table.items()): # tools is N-O
			self._tools_table.setdefault(gizmo, []).extend(reversed(tools)) # added in O-N order


