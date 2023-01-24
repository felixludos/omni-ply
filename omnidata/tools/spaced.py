from typing import Type, Callable, Any


from .base import RawCraft, CraftTool



class SpaceBase(CraftTool):
	def send_space_of(self, instance: Any, gizmo: str) -> Any:
		fn = getattr(instance, self._data['name'])
		return fn()



class Space(SpaceBase):
	pass



class space(RawCraft):
	_CraftItem = Space






