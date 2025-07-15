from .imports import *
from ..gears.op import Structured
from .geology import GeologistBase
from .gems import InheritableGem, FinalizedGem, LoopyGem, GeodeBase, ConfigGem, MechanismGeode



class Geologist(GeologistBase):
	pass



class gem(LoopyGem, ConfigGem, InheritableGem, FinalizedGem):
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


