from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable



class Gizmoed:
	def gizmos(self) -> Iterator[str]:
		raise NotImplementedError



class AbstractTool(Gizmoed): # leaf/source
	def get_from(self, ctx: 'AbstractTool', gizmo: str):
		raise NotImplementedError


	def __getitem__(self, gizmo: str):
		return self.get_from(self, gizmo)



class Tooled(Gizmoed):
	def tools(self) -> Iterator[AbstractTool]:
		raise NotImplementedError


	def vendors(self, gizmo: str) -> Iterator[AbstractTool]:
		raise NotImplementedError



class SingleVendor(Tooled):
	def vendor(self, gizmo: str, default: Any = None) -> AbstractTool:
		raise NotImplementedError

	def vendors(self, gizmo: str) -> Iterator[AbstractTool]:
		v = self.vendor(gizmo)
		if v is not None:
			yield v



class AbstractKit(Tooled, AbstractTool): # branch/router
	class MissingGizmo(KeyError):
		pass


	def gizmos(self) -> Iterator[str]:
		past = set()
		for tool in self.tools():
			for gizmo in tool.gizmos():
				if gizmo not in past:
					past.add(gizmo)
					yield gizmo

