from typing import Type, Optional, Any, TypeVar, Union, Iterable, Iterator, Dict, List, Tuple, Callable, Self
from omnibelt import unspecified_argument

T = TypeVar('T')


class AbstractGem:
	pass



class AbstractGeode(AbstractGem):
	pass



class AbstractGeologist:
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
