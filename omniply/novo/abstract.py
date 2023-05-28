from .imports import *
# from .errors import *



class AbstractTool:
	def gizmos(self) -> Iterator[str]:
		'''lists known products of this tool'''
		raise NotImplementedError


	def produces_gizmo(self, gizmo: str) -> bool:
		'''returns True if this tool can produce the given gizmo'''
		return gizmo in self.gizmos()


	def get_from(self, ctx: 'AbstractContext', gizmo: str) -> Any:
		'''returns the given gizmo from this tool, or raises ToolFailedError'''
		raise NotImplementedError



class AbstractToolKit(AbstractTool):
	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractTool]:
		'''returns all tools that can produce the given gizmo'''
		raise NotImplementedError



###########################################################################



class AbstractSpaced(AbstractTool):
	def space_of(self, gizmo: str):
		raise NotImplementedError


	def space_from(self, ctx: 'AbstractContext', gizmo: str) -> Any:
		raise NotImplementedError



class AbstractMultiTool(AbstractToolKit):
	def vendors(self, gizmo: str) -> Iterator[AbstractTool]:
		yield self



class AbstractContext(AbstractToolKit):
	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		raise NotImplementedError









