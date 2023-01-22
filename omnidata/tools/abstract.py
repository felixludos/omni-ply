from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable


class Gizmoed:
	def gizmos(self) -> Iterator[str]:
		raise NotImplementedError



class AbstractTool(Gizmoed): # leaf/source
	def get_from(self, ctx: 'AbstractTool', gizmo: str):
		raise NotImplementedError


	def __getitem__(self, gizmo: str):
		return self.get_from(self, gizmo)



class AbstractKit(AbstractTool): # branch/router
	def tools(self) -> Iterator[AbstractTool]:
		raise NotImplementedError


	def vendors(self, gizmo: str) -> Iterator[AbstractTool]:
		raise NotImplementedError


	class MissingGizmo(KeyError):
		pass


	def gizmos(self) -> Iterator[str]:
		past = set()
		for tool in self.tools():
			for gizmo in tool.gizmos():
				if gizmo not in past:
					past.add(gizmo)
					yield gizmo

