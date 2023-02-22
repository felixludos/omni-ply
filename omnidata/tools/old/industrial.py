from typing import Hashable
from collections import UserDict
from omnibelt.old_crafting import InitializationCrafty

from omnidata.features import Prepared

from omnidata.tools.abstract import AbstractKit, AbstractContext
from omnidata.tools.errors import MissingGizmoError
from .kits import CraftsKit


# class Industrial(AbstractKit): # gizmos come from crafts
# 	class Assembler(AbstractKit):
# 		pass


class AssemblerBase(AbstractContext, AbstractKit):
	def context_id(self) -> Hashable:
		return id(self)


	def tools(self):
		yield from self._tools


	def add_tool(self, tool):
		self._tools.append(tool)
	def add_tools(self, tools):
		self._tools.extend(tools)


	def __init__(self, tools=None, **kwargs):
		if tools is None:
			tools = []
		super().__init__(**kwargs)
		self._tools = tools


	def translation(self, **aliases):
		raise NotImplementedError # context manager with aliased assembler


class SizedAssembler(AssemblerBase):
	@property
	def size(self):
		return self._size

	def __init__(self, *args, size=None, **kwargs):
		super().__init__(**kwargs)
		self._size = size



class Cached(AssemblerBase, UserDict):
	def __init__(self, tools=None, manual=None):
		super().__init__(tools=tools, **manual)


	def _find_missing(self, gizmo):
		for tool in self.vendors(gizmo):
			val = tool[gizmo]
			self[gizmo] = val
			return val
		raise MissingGizmoError(gizmo)


	def __getitem__(self, item):
		if item in self.data:
			return self.data[item]
		return self._find_missing(item)



class Guru(SizedAssembler, Cached):
	def __init__(self, *tools, size=None, **manual):
		super().__init__(tools=list(tools), size=size, manual=manual)



class IndustrialBase(InitializationCrafty, Prepared):
	_Crafts = CraftsKit
	Guru = Guru


	def _prepare(self, *args, **kwargs):
		self._processed_crafts.prepare()


	def guru(self, *tools, **manual):
		return self.Guru(self._processed_crafts, *tools, **manual)



# class Guru(AbstractRouter): # fills in gizmos using the given router, and checks for cycles



# class Function(Industrial):
# 	@space('output')
# 	def dout(self):
# 		return None
#
# 	@space('input')
# 	def din(self):
# 		return None
#
# 	def __call__(self, inp):
# 		return self.Assembler(self, input=inp)['output']














