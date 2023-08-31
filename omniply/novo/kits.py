from .tools import *



# class KitBase(AbstractToolKit, ToolBase):
# 	pass



class Kit(AbstractToolKit, ToolBase):
	_tools_table: Dict[str, List[AbstractGadget]] # tools are kept in O-N order (reversed) for easy updates

	def __init__(self, *args, tools_table: Optional[Mapping] = None, **kwargs):
		if tools_table is None:
			tools_table = {}
		super().__init__(*args, **kwargs)
		self._tools_table = tools_table


	def gizmos(self) -> Iterator[str]:
		yield from self._tools_table.keys()


	def gives(self, gizmo: str) -> bool:
		return gizmo in self._tools_table


	def _vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		if gizmo is None:
			for tool in filter_duplicates(chain.from_iterable(map(reversed, self._tools_table.values()))):
				yield from tool.vendors(gizmo)
		else:
			if gizmo not in self._tools_table:
				raise self._MissingGizmoError(gizmo)
			for tool in filter_duplicates(reversed(self._tools_table[gizmo])):
				yield from tool.vendors(gizmo)


	_AssemblyFailedError = AssemblyFailedError
	def grab_from(self, ctx: 'AbstractGig', gizmo: str) -> Any:
		failures = []
		for tool in self._vendors(gizmo):
			try:
				return tool.grab_from(ctx, gizmo)
			except GadgetFailedError as e:
				e.tool = tool
				failures.append(e)
			except:
				prt.debug(f'{tool!r} failed while trying to produce: {gizmo!r}')
				raise
		if failures:
			raise self._AssemblyFailedError(gizmo, *failures)
		raise self._ToolFailedError(gizmo)



class LoopyKit(Kit):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._grabber_stack: Optional[Dict[str, Iterator[AbstractGadget]]] = {}


	def grab_from(self, ctx: 'AbstractGig', gizmo: str) -> Any:
		failures = []
		itr = self._grabber_stack.setdefault(gizmo, self._vendors(gizmo))
		# should be the same as Kit, except the iterators are cached until the gizmo is produced
		for tool in itr:
			try:
				out = tool.grab_from(ctx, gizmo)
			except GadgetFailedError as e:
				e.tool = tool
				failures.append(e)
			except:
				prt.debug(f'{tool!r} failed while trying to produce: {gizmo!r}')
				raise
			else:
				if gizmo in self._grabber_stack:
					self._grabber_stack.pop(gizmo)
				return out
		if gizmo in self._grabber_stack:
			self._grabber_stack.pop(gizmo)
		if failures:
			raise self._AssemblyFailedError(gizmo, *failures)
		raise self._ToolFailedError(gizmo)



class MutableKit(Kit):
	def include(self, *tools: Union[AbstractGadget, Callable]) -> 'MutableKit': # TODO: return Self
		'''adds given tools in reverse order'''
		return self.extend(tools)
		
		
	def extend(self, tools: Iterable[AbstractGadget]) -> 'MutableKit':
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


	def exclude(self, *tools: AbstractGadget) -> 'MutableKit':
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
			
		# convert crafts to skills and add in O-N order
		table = {}
		for key, craft in reversed(items.items()): # N-O
			skill = craft.as_skill(self)
			for gizmo in skill.gizmos():
				table.setdefault(gizmo, []).append(skill)
			
		# add N-O skills in reverse order for O-N _tools_table
		for gizmo, tools in table.items(): # tools is N-O
			self._tools_table.setdefault(gizmo, []).extend(tools) # added in O-N order


