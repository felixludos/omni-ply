from .imports import *
from omnibelt.crafts import AbstractSkill, AbstractCraft, AbstractCrafty, NestableCraft
from ..core.gaggles import LoopyGaggle
from ..core import Context as _Context, ToolKit as _ToolKit, Mechanism as _Mechanism, Gate as _Gate
from .abstract import AbstractGeared, AbstractMechanized
from .gearbox import MutableMechanics, GearedMechanism, CraftyGearedGaggle
from .mechanics import MechanizedBase, AutoMechanized, MechanizedGame, MutableMechanized, Mechanics
from .gears import GearDecorator
from .errors import GearFailed



class gear(GearDecorator):
	'''decorator for gears'''
	# from_context = GearDecorator # not included by default (but implemented)



class Mechanized(AutoMechanized, MutableMechanized):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.mechanize() # makes (local) gears cached by default



class ToolKit(CraftyGearedGaggle, _ToolKit): # no caching of gears and only local gears (no mechanics)
	pass



class Structured(AutoMechanized, MutableMechanized, ToolKit):
	pass



class Context(MechanizedGame, _Context):
	pass



class Mechanism(_Mechanism, GearedMechanism):
	_GearMechanism = _Mechanism



class Gate(_Gate, Mechanism):
	pass



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






