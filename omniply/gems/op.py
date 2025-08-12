from .imports import *
from ..gears.op import MechKit
from .geology import GeologistBase, StatefulGeologist
from .gems import InheritableGem, FinalizedGem, LoopyGem, GeodeBase, ConfigGem, MechanismGeode, GearGem



class Geologist(StatefulGeologist):
	pass



class Structured(MechKit, Geologist):
	pass



class gem(InheritableGem, FinalizedGem, LoopyGem, ConfigGem):
	def __get__(self, instance, owner):
		if instance is None:
			return self
		return self.resolve(instance)


	def __set__(self, instance, value):
		if instance is None:
			raise ValueError("instance must be not None")
		return self.revise(instance, value)


	def __delete__(self, instance):
		if instance is None:
			raise ValueError("instance must be not None")
		return self.remove(instance)



class geargem(InheritableGem, FinalizedGem, ConfigGem, GearGem):
	def __init__(self, gizmo: str, default: Optional[Any] = GearGem._no_value, **kwargs):
		super().__init__(gizmo=gizmo, default=default, **kwargs)

	def __get__(self, instance, owner):
		if instance is None:
			return self
		return self.resolve(instance)


	def __set__(self, instance, value):
		if instance is None:
			raise ValueError("instance must be not None")
		return self.revise(instance, value)


	def __delete__(self, instance):
		if instance is None:
			raise ValueError("instance must be not None")
		return self.remove(instance)




class geode(MechanismGeode, gem):
	pass


