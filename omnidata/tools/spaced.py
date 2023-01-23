from omnibelt.crafting import AbstractCrafts, AbstractCraft

from .abstract import AbstractSpaced, AbstractTool, AbstractKit
from .base import CraftsKit
from .errors import ToolFailedError



class SpacedKit(AbstractSpaced, AbstractKit):
	def space_of(self, gizmo: str) -> AbstractCrafts:
		for vendor in self.vendors(gizmo):
			try:
				return vendor.space_of(gizmo)
			except ToolFailedError:
				pass
		raise ToolFailedError(gizmo, f'No space for {gizmo!r}')



class SpacedTool(AbstractCraft, AbstractTool):
	def space_of(self, gizmo: str) -> AbstractCrafts:
		raise NotImplementedError



class SpacedCraftOperator():
	pass










