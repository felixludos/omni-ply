from typing import Type, Callable, Any


from .base import RawCraft, SpacedTool




class SpaceBase(SpacedTool):
	def send_space_of(self, instance: Any, gizmo: str) -> Any:
		fn = getattr(instance, self._data['name'])
		return fn()



class Space(SpaceBase):
	pass



class space(RawCraft):
	_CraftItem = Space



class SpatialRawCraft(RawCraft):  # decorator base
	_space_propagator = space

	def space(self, *args, **kwargs):
		return self._space_propagator(*args, **kwargs)




