from .imports import *
from .errors import *

T = TypeVar('T')



class AbstractQuirk:
	def setup(self, owner: Type[T], name: str) -> 'AbstractQuirk': # TODO: Self
		return self


	def resolve(self, instance: Optional[T] = None, owner: Optional[Type[T]] = None) -> Any:
		raise NotImplementedError


	def reset(self, instance: T, value: Optional[Any] = unspecified_argument) -> Any:
		raise NotImplementedError


	def rip(self, instance: Optional[T] = None) -> Any:
		raise NotImplementedError


	def replicate(self, **kwargs) -> Any:
		return self.__class__(**kwargs)



class ReplicatorQuirk(AbstractQuirk, Replicator):
	pass



# class ReferenceQuirk(AbstractQuirk):
# 	def reference(self, **update):
# 		raise NotImplementedError



class DescriptorQuirk(ReplicatorQuirk):
	def __init__(self, *, attrname: Optional[str] = None, **kwargs):
		super().__init__(**kwargs)
		self._attrname = attrname


	_MissingValueError = MissingValueError
	_MissingOwnerError = MissingOwnerError
	def setup(self, owner: Type[T], name: str) -> 'AbstractQuirk':
		if self._attrname is None:
			self._attrname = name
		elif name != self._attrname:
			raise TypeError(
				f"Cannot assign the same {self.__class__.__qualname__} to two different names "
				f"({self._attrname!r} and {name!r})."
			)
		return self


	def _replicator_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
		if 'attrname' not in kwargs:
			kwargs['attrname'] = self._attrname
		return kwargs


	def __str__(self):
		return f'<quirk:{self._attrname}>'


	def __repr__(self):
		return f'{self.__class__.__qualname__}({self._attrname})'


	def __set_name__(self, owner: Type[T], name: str):
		self.setup(owner, name)


	def __get__(self, instance: T, owner: Optional[Type[T]] = None) -> Any:
		return self.resolve(instance, owner=owner)


	def __set__(self, instance: T, value: Any):
		self.reset(instance, value)


	def __delete__(self, instance: T):
		self.rip(instance)



class OwnedDescriptorQuirk(DescriptorQuirk):
	def __init__(self, owner: Optional[Type[T]] = None, **kwargs):
		super().__init__(**kwargs)
		self._owner = owner


	def setup(self, owner: Type[T], name: str) -> 'AbstractQuirk': # TODO: Self
		self._owner = owner
		return super().setup(owner, name)


	def _replicator_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
		if 'owner' not in kwargs:
			kwargs['owner'] = self._owner
		return super()._replicator_kwargs(kwargs)


	def __str__(self):
		return f'<quirk:{self._owner.__qualname__}.{self._attrname}>'


	def __repr__(self):
		return f'{self.__class__.__name__}({self._owner.__qualname__}.{self._attrname})'



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


	def _replicator_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
		if 'default' not in kwargs:
			kwargs['default'] = self._default
		if 'getter' not in kwargs:
			kwargs['getter'] = self._getter
		return super()._replicator_kwargs(kwargs)


	def _check_fget(self, getter: Optional[Callable[[T], Any]] = None, default: Optional[Any] = unspecified_argument) \
			-> Tuple[Optional[Callable[[T], Any]], Optional[Any]]:
		if getter is None:
			if callable(default) and not isinstance(default, type) and default.__qualname__ != default.__name__:
				return default, self._missing_value  # decorator has no other args
			return None, default  # no getter provided (optionally can be added with __call__)
		return getter, default  # getter was specified as keyword argument


	def realize(self, instance: T, owner: Optional[Type[T]] = None) -> Any:
		if self._default is self._missing_value:
			raise self._MissingValueError(self)
		return self._default


	def resolve(self, instance: Optional[T] = None, owner: Optional[Type[T]] = None) -> Any:
		if self._getter is None:
			return self.realize(instance, owner=owner)
		if instance is None:
			raise self._MissingOwnerError(self)
		return self._getter.__get__(instance, owner=owner)()


	def getter(self, getter: Callable[[T], Any]) -> 'DefaultQuirk':
		return self.replicate(getter=getter)



class SetterQuirk(DescriptorQuirk):
	def __init__(self, *, setter: Optional[Callable[[T, Any], Any]] = None, **kwargs):
		super().__init__(**kwargs)
		self._setter = setter


	def _replicator_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
		if 'setter' not in kwargs:
			kwargs['setter'] = self._setter
		return super()._replicator_kwargs(kwargs)


	def reset(self, instance: T, value: Optional[Any] = unspecified_argument) -> Any:
		if instance is None:
			raise self._MissingOwnerError(self)
		if value is unspecified_argument:
			raise self._MissingValueError(self)
		if self._setter is not None:
			return self._setter.__get__(instance)(value)
		return super().reset(instance, value)


	def setter(self, setter: Callable[[T, Any], Any]) -> 'SetterQuirk':
		return self.replicate(setter=setter)



class DeleterQuirk(DescriptorQuirk):
	def __init__(self, *, deleter: Optional[Callable[[T], Any]] = None, **kwargs):
		super().__init__(**kwargs)
		self._deleter = deleter


	def _replicator_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
		if 'deleter' not in kwargs:
			kwargs['deleter'] = self._deleter
		return super()._replicator_kwargs(kwargs)


	def rip(self, instance: Optional[T] = None) -> Any:
		if instance is None:
			raise MissingOwnerError(self)
		if self._deleter is not None:
			return self._deleter.__get__(instance)()
		return super().rip(instance)


	def deleter(self, deleter: Callable[[T], Any]) -> 'DeleterQuirk':
		return self.replicate(deleter=deleter)



class CachedQuirk(DescriptorQuirk):
	def __init__(self, cache: bool = True, **kwargs):
		super().__init__(**kwargs)
		self._cache = cache


	def _replicator_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
		if 'cache' not in kwargs:
			kwargs['cache'] = self._cache
		return super()._replicator_kwargs(kwargs)


	def is_cached(self, instance: T) -> bool:
		return self._attrname in instance.__dict__


	def clear_cache(self, instance: T) -> 'CachedQuirk': # TODO: change to Self
		if self.is_cached(instance):
			del instance.__dict__[self._attrname]
		return self


	def _resolve(self, instance: T, owner: Optional[Type[T]] = None) -> Any:
		return super().resolve(instance, owner=owner)


	def _cache_value(self, instance: T, value: Any) -> Any:
		if instance is None:
			raise TypeError(f'Cannot cache {self} on class.')
		instance.__dict__[self._attrname] = value
		return value


	def resolve(self, instance: Optional[T] = None, owner: Optional[Type[T]] = None) -> Any:
		if self.is_cached(instance):
			# NOTE: this is usually redundant, since descriptor is called after __dict__ is checked
			return instance.__dict__[self._attrname]

		value = self._resolve(instance, owner=owner)
		return self._cache_value(instance, value) if self._cache else value


	def reset(self, instance: T, value: Optional[Any] = unspecified_argument) -> Any:
		self.clear_cache(instance)
		if value is not unspecified_argument:
			if self._cache:
				instance.__dict__[self._attrname] = value
				return value
			return super().reset(instance, value)


	def rip(self, instance: Optional[T] = None) -> Any:
		if self.is_cached(instance):
			del instance.__dict__[self._attrname]
		return super().rip(instance)



class UpdateQuirk(AbstractQuirk):
	def __init__(self, *, updater: Optional[Callable[[T, Any], Any]] = None, **kwargs):
		super().__init__(**kwargs)
		self._updater = updater


	def _replicator_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
		if 'updater' not in kwargs:
			kwargs['updater'] = self._updater
		return super()._replicator_kwargs(kwargs)


	def revise(self, instance: T, value: Any) -> Any:
		if self._updater is None:
			return value
		return self._updater.__get__(instance)(value)


	_IgnoreResetFlag = IgnoreResetFlag
	def reset(self, instance: T, value: Optional[Any] = unspecified_argument) -> Any:
		try:
			if value is not unspecified_argument:
				value = self.revise(instance, value)
		except self._IgnoreResetFlag:
			if value is not unspecified_argument:
				return value
		else:
			return super().reset(instance, value)


	def update(self, updater: Callable[[T, Any], Any]) -> 'UpdateQuirk':
		return self.replicate(updater=updater)



class InheritableQuirk(AbstractQuirk):
	def inherit(self, owner: Union[T, Type[T]]) -> bool:
		return False



class HiddenQuirk(AbstractQuirk):
	def hidden(self, owner: Union[T, Type[T]]) -> bool:
		return False



class SimpleQuirk(UpdateQuirk, CachedQuirk, DefaultQuirk, SetterQuirk, DeleterQuirk, InheritableQuirk, HiddenQuirk):
	def __init__(self, *, inherit: bool = False, hidden: bool = False, **kwargs):
		super().__init__(**kwargs)
		self._inherit = inherit
		self._hidden = hidden


	# def resolve(self, instance: Optional[T] = None, owner: Optional[Type[T]] = None) -> Any:
	# 	if instance is None:
	# 		return self
	# 	return super().resolve(instance, owner=owner)


	def _replicator_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
		if 'inherit' not in kwargs:
			kwargs['inherit'] = self._inherit
		if 'hidden' not in kwargs:
			kwargs['hidden'] = self._hidden
		return super()._replicator_kwargs(kwargs)


	def inherit(self, owner: Union[T, Type[T]]) -> bool:
		return self._inherit


	def hidden(self, owner: Union[T, Type[T]]) -> bool:
		return self._hidden












