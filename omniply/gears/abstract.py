from .imports import *



class AbstractGear(AbstractGadget):
	pass



class AbstractGearbox(AbstractGaggle):
	'''just like a mutable gaggle, but adds gearboxes when encountering geared gadgets'''
	pass



class AbstractGeared(AbstractGadget):
	def gears(self) -> Iterator[str]:
		yield from self.gearbox().gizmos()


	def gearbox(self) -> AbstractGearbox:
		raise NotImplementedError



class AbstractMechanical(AbstractGadget):
	'''gadget with synchronized gears'''
	def mechanics(self) -> Optional['AbstractMechanics']:
		raise NotImplementedError



class AbstractMechanics(AbstractGame):
	'''a context, buf for gears'''
	pass



class AbstractMechanized(AbstractMechanical):
	def mechanize(self, mechanics: AbstractMechanics):
		raise NotImplementedError




