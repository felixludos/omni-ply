
from .imports import *


T = TypeVar('T')



class AbstractQuirk:
	def __set_name__(self, owner, name):
		raise NotImplementedError


	def __get__(self, instance, owner):
		raise NotImplementedError


	def __set__(self, instance, value):
		raise NotImplementedError


	def __delete__(self, instance):
		raise NotImplementedError



class DescriptorQuirk(AbstractQuirk):
	_attrname = None

	def __str__(self):
		return f'<quirk:{self._attrname}>'


	def __repr__(self):
		return f'{self.__class__.__qualname__}({self._attrname})'


	def __set_name__(self, owner: Type[T], name: str):
		if self._attrname is None:
			self._attrname = name
		elif name != self._attrname:
			raise TypeError(
				f"Cannot assign the same {self.__class__.__qualname__} to two different names "
				f"({self._attrname!r} and {name!r})."
			)
		return self


	def __get__(self, instance: T, owner: Optional[Type[T]] = None) -> Any:
		return self.resolve(instance, owner=owner)


	def __set__(self, instance: T, value: Any):
		self.reset(instance, value)


	def __delete__(self, instance: T):
		self.rip(instance)





