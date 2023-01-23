from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

from .. import spaces

from .errors import ToolFailedError



class Gizmoed:
	def gizmos(self) -> Iterator[str]:
		raise NotImplementedError



class Tooled(Gizmoed):
	def tools(self) -> Iterator['AbstractTool']:
		raise NotImplementedError


	def vendors(self, gizmo: str) -> Iterator['AbstractTool']:
		raise NotImplementedError



class SingleVendor(Tooled):
	def vendor(self, gizmo: str, default: Any = None) -> 'AbstractTool':
		raise NotImplementedError


	def vendors(self, gizmo: str) -> Iterator['AbstractTool']:
		v = self.vendor(gizmo)
		if v is not None:
			yield v



class AbstractTool(Gizmoed): # leaf/source
	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str):
		raise NotImplementedError


	def __getitem__(self, gizmo: str):
		return self.get_from(None, gizmo)



class AbstractContext(AbstractTool):
	def __getitem__(self, gizmo: str):
		return self.get_from(self, gizmo)



class AbstractKit(Tooled, AbstractTool): # branch/router
	def gizmos(self) -> Iterator[str]:
		past = set()
		for tool in self.tools():
			for gizmo in tool.gizmos():
				if gizmo not in past:
					past.add(gizmo)
					yield gizmo


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str):
		tries = 0
		for vendor in self.vendors(gizmo):
			try:
				return vendor.get_from(ctx, gizmo)
			except ToolFailedError:
				tries += 1
		raise ToolFailedError(f'No vendor for {gizmo} in {self} (tried {tries} vendor/s)')



class AbstractSpaced(AbstractTool):
	def space_of(self, gizmo: str) -> spaces.Dim:
		raise NotImplementedError








