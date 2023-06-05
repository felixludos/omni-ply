from .imports import *



class AbstractTool:
	def gizmos(self) -> Iterator[str]:
		'''lists known products of this tool'''
		raise NotImplementedError


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str,
	             default: Optional[Any] = unspecified_argument) -> Any:
		'''returns the given gizmo from this tool, or raises ToolFailedError'''
		raise NotImplementedError


	def vendors(self, gizmo: Optional[str] = None) -> Iterator['AbstractTool']:
		'''returns all known tools that can produce the given gizmo'''
		yield self


	def produces_gizmo(self, gizmo: str) -> bool:
		'''returns True if this tool can produce the given gizmo'''
		return gizmo in self.gizmos()


	def __repr__(self):
		return f'{self.__class__.__name__}({", ".join(map(str, self.gizmos()))})'



class AbstractToolKit(AbstractTool):
	def gizmos(self) -> Iterator[str]:
		'''lists known products of this tool'''
		raise NotImplementedError


	def tools(self, gizmo: Optional[str] = None) -> Iterator[AbstractTool]:
		'''returns all known tools/kits in this kit'''
		raise NotImplementedError


	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractTool]:
		'''returns all known tools that can produce the given gizmo'''
		for vendor in self.tools(gizmo):
			yield from vendor.vendors(gizmo)



###########################################################################



class AbstractMultiTool(AbstractToolKit):
	'''a special kind of kit that doesn't allow subtools to be accessed directly through vendors()'''
	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractTool]:
		yield self



class AbstractContext(AbstractToolKit):
	'''
	Contexts are a specific type of tool kit which takes ownership of a get_from call,
	rather than (usually) silently delegating to an appropriate tool.

	That means in general, a kit's get_from method is not called directly, but rather the containing
	tools are accessed through the kit's vendors method.

	It's the context that dictates how it's members are used to produce a gizmo.
	'''
	# def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractTool]:
	# 	'''returns all tools that can produce a gizmo recursively'''
	# 	for vendor in self.gadgets(gizmo):
	# 		yield from vendor.vendors(gizmo)


	def package(self, val: Any, gizmo: Optional[str] = None) -> Any:
		return val




class AbstractGang(AbstractContext, AbstractMultiTool):
	def gizmoto(self) -> Iterator[str]:
		yield from super().gizmos()


	def gizmos(self) -> Iterator[str]:
		for gizmo in self.gizmoto():
			yield self.gizmo_to(gizmo)


	def gizmo_from(self, gizmo: str) -> str:
		raise NotImplementedError


	def gizmo_to(self, external: str) -> str:
		raise NotImplementedError





