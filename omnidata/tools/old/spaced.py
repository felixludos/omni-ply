from typing import Type, Callable, Any
from omnibelt import agnosticproperty

from .base import RawCraft, SpacedTool



class Space(SpacedTool):
	pass



class space(RawCraft):
	_CraftItem = Space



class SpatialRawCraft(RawCraft):  # decorator base
	_space_propagator = space

	@agnosticproperty
	def space(self):
		return self._agnostic_propagator('space', propagation_type=space)




