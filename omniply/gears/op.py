from .imports import *
from omnibelt.crafts import AbstractSkill, AbstractCraft, AbstractCrafty, NestableCraft
from ..core.gaggles import LoopyGaggle
from ..core import Context, ToolKit as _ToolKit
from .gearbox import MutableGearbox, GearedGaggle
from .mechanics import MechanizedBase, AutoMechanized, Mechanics
from .gears import AutoGearDecorator, GearDecorator



class gear(AutoGearDecorator):
	'''decorator for gears'''
	from_context = GearDecorator



class Geared(GearedGaggle):
	'''gaggle which can contain gears and produces a gearbox'''
	pass



class Mechanized(Geared, MechanizedBase):
	'''synchronized'''
	pass



class ToolKit(AutoMechanized, Geared, _ToolKit):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._mechanize_self()






######################################################################



# class SpaceSelection(GaggleBase, AbstractGame):
# 	def __init__(self, src: 'Spaced', **kwargs):
# 		super().__init__(**kwargs)
# 		self.src = src
#
#
# 	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
# 		"""
# 		Transforms the given context `ctx` to produce the specified `gizmo`, or raises ToolFailedError.
# 		The context can be expected to contain all the necessary input gizmos.
#
# 		This method should be overridden by subclasses to provide the actual implementation.
#
# 		Args:
# 			ctx (Optional['AbstractGame']): The context from which to grab any necessary input gizmos.
# 			gizmo (str): The gizmo that must be produced.
#
# 		Returns:
# 			Any: The specified output gizmo.
#
# 		Raises:
# 			ToolFailedError: If the gizmo cannot be grabbed (possibly because a necessary input gizmo is missing).
# 		"""
# 		raise NotImplementedError
#
#
#
# class SpaceCraft(AbstractCraft):
#
#
#
# 	pass
#
#
#
# class Spaced(ToolKit):
# 	_Spaces = SpaceSelection
# 	def spaces(self) -> SpaceSelection:
# 		return self._Spaces(self)
#
#
# class Structured(Spaced):
# 	_structure = None






