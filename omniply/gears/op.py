from .imports import *
from omnibelt.crafts import AbstractSkill, AbstractCraft, AbstractCrafty, NestableCraft

from ..core.gaggles import GaggleBase



class gear:
	pass



class Geared:
	pass



class Mechanized:
	pass



class Mechanics:
	pass



######################################################################



class SpaceSelection(GaggleBase, AbstractGame):
	def __init__(self, src: 'Spaced', **kwargs):
		super().__init__(**kwargs)
		self.src = src


	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
		"""
		Transforms the given context `ctx` to produce the specified `gizmo`, or raises ToolFailedError.
		The context can be expected to contain all the necessary input gizmos.

		This method should be overridden by subclasses to provide the actual implementation.

		Args:
			ctx (Optional['AbstractGame']): The context from which to grab any necessary input gizmos.
			gizmo (str): The gizmo that must be produced.

		Returns:
			Any: The specified output gizmo.

		Raises:
			ToolFailedError: If the gizmo cannot be grabbed (possibly because a necessary input gizmo is missing).
		"""
		raise NotImplementedError



class SpaceCraft(AbstractCraft):



	pass



class Spaced(ToolKit):
	_Spaces = SpaceSelection
	def spaces(self) -> SpaceSelection:
		return self._Spaces(self)


class Structured(Spaced):
	_structure = None






