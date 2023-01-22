from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type
from .abstract import AbstractTool, AbstractKit



class SkippableTool(AbstractTool):
	class SkipTool(ValueError):
		pass



class ToolBase(SkippableTool, AbstractTool):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)



class KitBase(SkippableTool, AbstractKit):
	def __init__(self, *tools, aliases=None, **kwargs):
		if aliases is None:
			aliases = {}
		super().__init__(**kwargs)
		self._aliases = aliases
		self._reverse_aliases = {v: k for k, v in reversed(aliases.items())}
		self._tools = tools
		self._vendors = {}
		for tool in self.tools():
			for gizmo in tool.gizmos():
				self._vendors.setdefault(gizmo, []).append(tool)


	def tools(self) -> Iterator[AbstractTool]:
		yield from reversed(self._tools)


	def vendors(self, gizmo: str) -> Iterator[AbstractTool]:
		yield from self._vendors.get(gizmo, ())


	def get_from(self, ctx: 'AbstractTool', gizmo: str):
		key = self.gizmoto(gizmo)
		for vendor in self.vendors(key):
			try:
				return vendor.get_from(ctx, key)
			except self.SkipTool:
				pass
		raise self.MissingGizmo(gizmo)


	def gizmoto(self, gizmo: str) -> str: # check aliases (for getting)
		return self._aliases.get(gizmo, gizmo)


	def gizmofrom(self, gizmo: str) -> str: # invert aliases (for setting)
		return self._reverse_aliases.get(gizmo, gizmo)



class Industrial(AbstractKit): # gizmos come from crafts
	class Assembler(AbstractKit):
		pass

# class Guru(AbstractRouter): # fills in gizmos using the given router, and checks for cycles



class Function(Industrial):
	@machine.space('output')
	def dout(self):
		return None

	@machine.space('input')
	def din(self):
		return None

	def __call__(self, inp):
		return self.Assembler(self, input=inp)['output']




