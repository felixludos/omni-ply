from .imports import *



class AbstractGear(AbstractGadget):
	pass



class AbstractGearbox(AbstractGaggle):
	pass



class AbstractGearable(AbstractGadget):
	def gears(self) -> Iterator[str]:
		raise NotImplementedError



class AbstractGeared(AbstractGearable):
	# analogous to "prepared"
	# _structure = None
	def gearbox(self) -> AbstractGearbox:
		raise NotImplementedError


class AbstractMechanics(AbstractGame):
	'''a context, buf for gears'''
	pass


class MechanizedBase:
	_mechanics = None

	def mechanize(self, mechanics: AbstractMechanics):
		self._mechanics = mechanics

	pass



