from .imports import *
from ..gears.op import Structured
from .geology import GeologistBase
from .gems import InheritableGem, FinalizedGem, CachableGem, GeodeBase



class Geologist(GeologistBase):
	pass



class gem(InheritableGem, FinalizedGem, CachableGem):
	def __get__(self, instance, owner):
		return self.resolve(instance)


	def __set__(self, instance, value):
		return self.revise(instance, value)


	def __delete__(self, instance):
		return self.remove(instance)



class geode(GeodeBase, gem):
	pass


