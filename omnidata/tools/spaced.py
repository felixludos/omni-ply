from typing import Type, Callable, Any

from .base import RawCraft, SpacedTool



class Space(SpacedTool):
	pass



class space(RawCraft):
	_CraftItem = Space



class SpatialRawCraft(RawCraft):  # decorator base
	_space_propagator = space

	def space(self, *args, **kwargs):
		fn, args = self._filter_callable_arg(args)
		if fn is not None:
			return self._space_propagator(*self._args, **kwargs)(fn)
		return self._space_propagator(*args, **kwargs)




