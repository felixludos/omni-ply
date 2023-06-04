from .imports import *



class AbstractTool:
	def gizmos(self) -> Iterator[str]:
		'''lists known products of this tool'''
		raise NotImplementedError


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str,
	             default: Optional[Any] = unspecified_argument) -> Any:
		'''returns the given gizmo from this tool, or raises ToolFailedError'''
		raise NotImplementedError


	def vendors(self, gizmo: str) -> Iterator['AbstractTool']:
		'''returns all tools that can produce the given gizmo'''
		yield self


	def vendors_terminal(self, gizmo: str) -> Iterator['AbstractTool']:
		'''returns all tools that can produce a gizmo recursively'''
		yield self


	def produces_gizmo(self, gizmo: str) -> bool:
		'''returns True if this tool can produce the given gizmo'''
		return gizmo in self.gizmos()


	def __repr__(self):
		return f'{self.__class__.__name__}({", ".join(map(str, self.gizmos()))})'



class AbstractToolKit(AbstractTool):
	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractTool]:
		'''returns all tools that can produce the given gizmo'''
		raise NotImplementedError


	def vendors_terminal(self, gizmo: Optional[str] = None) -> Iterator[AbstractTool]:
		'''returns all tools that can produce a gizmo recursively'''
		for vendor in self.vendors(gizmo):
			yield from vendor.vendors_terminal(gizmo)



###########################################################################




class AbstractMultiTool(AbstractToolKit):
	def vendors(self, gizmo: str) -> Iterator[AbstractTool]:
		yield self



class AbstractContext(AbstractToolKit):
	# def get_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
	# 	raise NotImplementedError


	def package(self, src: AbstractTool, gizmo: str, val: Any) -> Any:
		return val









