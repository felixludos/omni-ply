from .imports import *
from .abstract import AbstractMechanized, AbstractMechanics
from ..core import Context
from .gearbox import MutableMechanics



# class Mechanics(Context, LoopyGaggle, MutableGearbox):
class Mechanics(Context, MutableMechanics, AbstractMechanics):
	'''context of gears'''
	pass



class MechanizedBase(AbstractMechanized):
	_mechanics = None

	def mechanics(self) -> Optional[AbstractMechanics]:
		return self._mechanics

	def mechanize(self, mechanics: AbstractMechanics):
		self._mechanics = mechanics
		return self



class AutoMechanized(MechanizedBase):
	_Mechanics = Mechanics
	def _auto_mechanics(self):
		return self._Mechanics(self)

	def mechanize(self, mechanics: AbstractMechanics = None):
		if mechanics is None:
			mechanics = self._auto_mechanics()
		return super().mechanize(mechanics)



class MechanizedGaggle(MechanizedBase):
	def mechanize(self, mechanics: AbstractMechanics):
		for gadget in self.vendors():
			if isinstance(gadget, AbstractMechanized):
				gadget.mechanize(mechanics)
		return super().mechanize(mechanics)



class AutoMechanizedGaggle(AutoMechanized, MechanizedGaggle):
	def _auto_mechanics(self):
		return self._Mechanics(*self.vendors())



