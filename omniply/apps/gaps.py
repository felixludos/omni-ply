
from .. import AbstractGadget, AbstractGaggle
from ..core.gaggles import CraftyGaggle


class AbstractGauge(AbstractGadget):
	def em(self, internal_gizmo: str) -> str:
		'''Converts an internal gizmo to its external representation.'''
		raise NotImplementedError


	def va(self, external_gizmo: str) -> str:
		'''Converts an external gizmo to its internal representation.'''
		raise NotImplementedError



class AbstractGauged(CraftyGaggle):

	def _process_crafts(self):
		'''Processes the crafts in the tool kit.'''
		pass


	pass



