from .imports import *
from ..core.gaggles import MutableGaggle, CraftyGaggle
from ..core import Context, ToolKit
from .abstract import AbstractMechanized, AbstractMechanical, AbstractGearbox, AbstractGeared, AbstractGear
from .gears import GearCraft

# TODO: include a back reference of Gearboxes to their owners (for exclude)



class MutableGearbox(MutableGaggle, AbstractGearbox):
	'''A mutable gaggle that includes gearboxes from included gadgets that are geared'''
	def extend(self, gadgets: Iterable[AbstractGadget]) -> Self:
		return super().extend(gadget.gearbox() if isinstance(gadget, AbstractGeared) else gadget
							  for gadget in gadgets)


	def exclude(self, *gadgets: AbstractGadget) -> Self:
		raise NotImplemented('not supported yet') # TODO



class GearedGaggle(CraftyGaggle, AbstractGeared):
	_gears_list: list[AbstractGear] = None


	def _process_crafts(self):
		self._gears_list = []
		super()._process_crafts()


	def _process_skill(self, skill):
		if isinstance(skill, AbstractGear):
			self._gears_list.append(skill)
		else:
			self.include(skill)


	_Gearbox = ToolKit
	def gearbox(self) -> AbstractGearbox:
		return self._Gearbox(*self._gears_list)

