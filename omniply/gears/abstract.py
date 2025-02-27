from .imports import *



class AbstractGear(AbstractGadget):
	def update_cache(self, value: Any):
		raise NotImplementedError



class AbstractGearbox(AbstractGaggle):
	'''just like a mutable gaggle, but adds gearboxes when encountering geared gadgets'''
	pass



class AbstractGeared(AbstractGadget):
	def gears(self) -> Iterator[str]:
		yield from self.gearbox().gizmos()


	def gearbox(self) -> AbstractGearbox:
		raise NotImplementedError




class AbstractMechanical(AbstractGadget): # TODO: probably should be a subclass of AbstractGeared (?)
	'''gadget with synchronized gears'''
	def mechanics(self) -> Optional['AbstractMechanics']:
		raise NotImplementedError



class AbstractMechanics(AbstractGame):
	'''a context, buf for gears'''
	pass



class AbstractMechanized(AbstractMechanical):
	def mechanize(self, mechanics: AbstractMechanics):
		raise NotImplementedError




