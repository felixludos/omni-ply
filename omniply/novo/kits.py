from .imports import *

from .abstract import *
from .errors import *
from .tools import *



class Kit(AbstractToolKit, MyAbstractTool):
	_tools_table: Dict[str, List[AbstractTool]]

	def __init__(self, tools_table: Optional[Mapping] = None, **kwargs):
		if tools_table is None:
			tools_table = {}
		super().__init__(**kwargs)
		self._tools_table = tools_table


	def gizmos(self) -> Iterator[str]:
		yield from self._tools_table.keys()


	def produces_gizmo(self, gizmo: str) -> bool:
		return gizmo in self._tools_table


	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractTool]:
		if gizmo is None:
			yield from filter_duplicates(chain.from_iterable(self._tools_table.values()))
		else:
			if gizmo not in self._tools_table:
				raise self._MissingGizmoError(gizmo)
			yield from self._tools_table[gizmo]


	_AssemblyFailedError = AssemblyFailedError
	def get_from(self, ctx: 'AbstractContext', gizmo: str) -> Any:
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


	def get_from(self, ctx: 'AbstractContext', gizmo: str) -> Any:
		failures = []
		itr = self._get_from_status.setdefault(gizmo, self.vendors(gizmo))
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


	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractTool]:
		if gizmo is None:
			yield from filter_duplicates(chain.from_iterable(map(reversed, self._tools_table.values())))
		else:
			if gizmo not in self._tools_table:
				raise self._MissingGizmoError(gizmo)
			yield from reversed(self._tools_table[gizmo])



class Context(AbstractContext):
	def get(self, gizmo: str, default: Any = unspecified_argument):
		try:
			return self.get_from(None, gizmo)
		except ToolFailedError:
			if default is unspecified_argument:
				raise
			return default


	def __getitem__(self, item):
		return self.get(item)


	def _get_from_fallback(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		return ctx.get_from(self, gizmo)


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		try:
			return super().get_from(self, gizmo)
		except ToolFailedError:
			if ctx is None or ctx is self:
				raise
			return self._get_from_fallback(ctx, gizmo)



class TwostageContext(AbstractContext):
	'''splits the get_from into a public and protected method'''
	def _get_from(self, ctx: AbstractContext, gizmo: str) -> Any:
		return super().get_from(ctx, gizmo)


	def get_from(self, ctx: Optional[AbstractContext], gizmo: str) -> Any:
		return self._get_from(ctx, gizmo)



class Cached(TwostageContext, UserDict):
	def __repr__(self):
		gizmos = [(gizmo if self.is_cached(gizmo) else '{' + gizmo + '}') for gizmo in self.gizmos()]
		return f'{self.__class__.__name__}({", ".join(gizmos)})'


	def gizmos(self) -> Iterator[str]:
		yield from filter_duplicates(self.cached(), super().gizmos())


	def is_cached(self, gizmo: str) -> bool:
		return gizmo in self.data


	def cached(self) -> Iterator[str]:
		yield from self.data.keys()


	def clear_cache(self) -> None:
		self.data.clear()


	def _find_from(self, ctx: AbstractContext, gizmo: str) -> Any:
		val = super()._get_from(ctx, gizmo)
		self.data[gizmo] = val  # cache loaded val
		return val


	def _get_from(self, ctx: AbstractContext, gizmo: str) -> Any:
		val = self.data[gizmo] if self.is_cached(gizmo) else self._find_from(ctx, gizmo)
		# return val if ctx is self else ctx.package(self, gizmo, val)
		return val









