from .imports import *
from .abstract import AbstractMechanized, AbstractMechanics
from ..core import Context
from .gearbox import MutableGearbox



# class Mechanics(Context, LoopyGaggle, MutableGearbox):
class Mechanics(Context, MutableGearbox, AbstractMechanics):
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
	def _mechanize_self(self):
		self._mechanics = Mechanics(self)


	def mechanize(self, mechanics: AbstractMechanics = None):
		if mechanics is None:
			self._mechanize_self()
		return super().mechanize(mechanics)

