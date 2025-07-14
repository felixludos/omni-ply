from typing import Type, Optional, Any, TypeVar, Union, Iterable, Iterator, Dict, List, Tuple, Callable, Self, Mapping
from omnibelt import unspecified_argument
from omnibelt.crafts import InheritableCrafty


T = TypeVar('T')


class AbstractGem:
	@property
	def inherit(self):
		raise NotImplementedError
	
	def reconstruct(self, instance):
		"""called in __init__ of the geologist to set up the gem"""
		pass
	
	def revitalize(self, instance):
		"""after construction, this is called if no value is provided to enable eager resolution"""
		pass

	def resolve(self, instance):
		raise NotImplementedError

	def revise(self, instance, value):
		raise NotImplementedError
	
	def remove(self, instance):
		"""called when the gem is removed from the geologist"""
		pass


class AbstractGeode(AbstractGem):
	def restage(self, instance, scape: Mapping[str, Any] = None):
		"""called during stage() the geologist in case the underlying geode needs to be staged"""
		return None
	
	
	def relink(self, instance: 'AbstractGeologist') -> Iterator['AbstractGadget']:
		raise NotImplementedError



class AbstractGeologist(InheritableCrafty):
	def refresh_geodes(self, *names: str):
		pass



# class AbstractQuirk:
# 	def register(self, owner: Type[T], name: str) -> Self: # TODO: Self
# 		return self
#
#
# 	def resolve(self, instance: Optional[T] = None) -> Any:
# 		raise NotImplementedError
#
#
# 	def reset(self, instance: T, value: Optional[Any] = unspecified_argument) -> Any:
# 		raise NotImplementedError
#
#
# 	def rip(self, instance: Optional[T] = None) -> Any:
# 		raise NotImplementedError



# class AbstractReplicatable(AbstractQuirk):
# 	def replicate(self, **kwargs) -> Any:
# 		return self.__class__(**kwargs)



# class AbstractBuildable(AbstractQuirk):
# 	def realize(self, instance: Optional[T] = None) -> Any:
# 		raise NotImplementedError
