from .imports import *
from .abstract import AbstractQuirk, T



class MissingValueError(KeyError):
	pass


class DescriptorQuirk(AbstractQuirk):
	def __init__(self, *, attrname: Optional[str] = None, owner: Optional[Type[T]] = None, **kwargs):
		super().__init__(**kwargs)
		self._attrname = attrname
		self._owner = owner


	def _replicator_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
		if 'attrname' not in kwargs:
			kwargs['attrname'] = self._attrname
		return kwargs


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
		self._owner = owner
		return self


	def __get__(self, instance: T, owner: Optional[Type[T]] = None) -> Any:
		if self._getter is None:
			return self.realize(instance, owner=owner)
		if instance is None:
			raise self._MissingOwnerError(self)
		return self._getter.__get__(instance, owner=owner)()


	def __set__(self, instance: T, value: Any):
		self.reset(instance, value)


	def __delete__(self, instance: T):
		self.rip(instance)



class DefaultQuirk(DescriptorQuirk):
	_missing_value = object()

	def __init__(self, default: Optional[Any] = unspecified_argument, *,
	             getter: Optional[Callable[[T], Any]] = None, **kwargs):
		if default is unspecified_argument:
			default = self._missing_value
		getter, default = self._check_fget(getter, default)
		super().__init__(**kwargs)
		self._default = default
		self._getter = getter


	_MissingValueError = MissingValueError
	def realize(self, instance: T, owner: Optional[Type[T]] = None) -> Any:
		if self._default is self._missing_value:
			raise self._MissingValueError(self)
		return self._default


	def __get__(self, instance: T, owner: Optional[Type[T]] = None) -> Any:
		if self._getter is None:
			return self.realize(instance, owner=owner)
		if instance is None:
			raise self._MissingOwnerError(self)
		return self._getter.__get__(instance, owner=owner)()

	pass











