from .imports import *
from ..core.gaggles import MutableGaggle, CraftyGaggle
from ..core.gangs import GangBase
from ..core import Context, ToolKit, Gang, Gate
from .abstract import AbstractMechanized, AbstractMechanics, AbstractMechanical, AbstractGearbox, AbstractGeared, AbstractGear
from .gears import GearCraft, GearFailed

# TODO: include a back reference of Gearboxes to their owners (for exclude)



class GearBox(ToolKit, AbstractGearbox):
	def __init__(self, *gears: AbstractGear, base: AbstractGeared = None, **kwargs):
		super().__init__(*gears, **kwargs)
		self._base = base



class MutableMechanics(MutableGaggle, AbstractMechanics):
	'''A mutable gaggle that includes gearboxes from included gadgets that are geared'''
	def extend(self, gadgets: Iterable[AbstractGadget]) -> Self:
		return super().extend(gadget.gearbox() if isinstance(gadget, AbstractGeared) else gadget
							  for gadget in gadgets)


	def exclude(self, *gadgets: AbstractGadget) -> Self:
		raise NotImplemented('not supported yet') # TODO



class GearedGaggle(AbstractGeared, AbstractGaggle):
	_GearFailed = GearFailed
	_GearBox = GearBox
	def gearbox(self, *args, **kwargs) -> AbstractGearbox:
		return self._GearBox(*args, base=self, **kwargs).extend(
			gadget.gearbox() for gadget in self.vendors() if isinstance(gadget, AbstractGeared))

		# gearbox = self._GearBox(*self._gears_list, base=self)
		# for gadget in self.vendors():
		# 	if isinstance(gadget, AbstractGeared):
		# 		gearbox.extend(gadget.gearbox().vendors())
		# return gearbox



class CraftyGearedGaggle(CraftyGaggle, GearedGaggle):
	'''gaggle which can contain gears and produces a gearbox'''
	_gears_list: list[AbstractGear] = None


	def _process_crafts(self):
		if self._gears_list is None:
			self._gears_list = []
		super()._process_crafts()


	def _process_skill(self, skill):
		if isinstance(skill, AbstractGear):
			self._gears_list.append(skill)
		else:
			super()._process_skill(skill)


	def gearbox(self) -> AbstractGearbox:
		return super().gearbox(*self._gears_list)



class GearedGang(GangBase, GearedGaggle):
	_GearGang = None
	def gearbox(self) -> AbstractGearbox:
		return self._GearGang(super().gearbox(), aus=self._aus_gang, ein=self._ein_gang,
							  exclusive=self._exclusive, insulated=self._insulated)




