from .imports import *
from .abstract import AbstractMechanized, AbstractMechanics
from ..core import Context
from ..core.gaggles import AbstractGaggle, MutableGaggle
from .gearbox import MutableMechanics



class Mechanics(Context, MutableMechanics, AbstractMechanics):
	'''context of gears'''
	pass


class MechanizedBase(AbstractMechanized):
	_mechanics: Mechanics = None


	def mechanics(self) -> Optional[AbstractMechanics]:
		return self._mechanics


	def mechanize(self, mechanics: Mechanics):
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



class MechanizedGaggle(MechanizedBase, AbstractGaggle):
	def mechanize(self, mechanics: Mechanics):
		for gadget in self.vendors():
			if isinstance(gadget, AbstractMechanized):
				gadget.mechanize(mechanics)
		return super().mechanize(mechanics)



class MutableMechanized(MechanizedGaggle, MutableGaggle):
	def extend(self, gadgets: Iterable[AbstractGadget]):
		out = super().extend(gadgets)
		if self._mechanics is not None:
			self._mechanics.extend(gadgets)
			for gadget in gadgets:
				if isinstance(gadget, AbstractMechanized):
					gadget.mechanize(self._mechanics)
		return out



class MechanizedGame(AutoMechanized, MutableMechanized):
	'''for games'''
	def _auto_mechanics(self):
		return self._Mechanics(*self.vendors())



