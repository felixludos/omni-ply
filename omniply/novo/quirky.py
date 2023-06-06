from .imports import *

from .quirks import *


class AbstractQuirky:
	def fill_quirks(self, fn, args=None, kwargs=None, **finder_kwargs) -> Dict[str, Any]:
		raise NotImplementedError


	def _extract_quirks(self, kwargs):
		raise NotImplementedError


	# def _existing_quirks(self, *, hidden=False):
	# 	for key, param in self.named_quirks(hidden=hidden):
	# 		if param.is_missing(self):
	# 			yield key, getattr(self, key)


	def has_quirk(self, key):
		return isinstance(self.get_quirk(key, None), AbstractQuirk)


	def get_quirk(self, key, default=unspecified_argument):
		raise NotImplementedError


	@agnostic
	def quirks(self, *, hidden=False):
		for key, val in self.named_quirks(hidden=hidden):
			yield val


	@agnostic
	def named_quirks(self, *, hidden=False): # N-O
		raise NotImplementedError


	@agnostic
	def quirk_names(self, *, hidden=False):
		for key, val in self.named_quirks(hidden=hidden):
			yield key



class Quirky(AbstractQuirky):
	def __init__(self, *args, **kwargs):
		params, remaining = self._extract_quirks(kwargs)
		super().__init__(*args, **remaining)
		for name, value in params.items():
			setattr(self, name, value)


	class _find_missing_quirk:
		def __init__(self, base, **kwargs):
			super().__init__(**kwargs)
			self.base = base


		def __call__(self, name, default=inspect.Parameter.empty):
			value = getattr(self.base, name, default)
			if value is inspect.Parameter.empty:
				raise KeyError(name)
			return value


	def fill_quirks(self, fn, args=None, kwargs=None, **finder_kwargs) -> Dict[str, Any]:
		params = extract_function_signature(fn, args=args, kwargs=kwargs, allow_positional=False,
		                                    default_fn=self._find_missing_quirk(self), **finder_kwargs)

		return params


	def _extract_quirks(self, kwargs):
		params = {}
		for name, _ in self.named_quirks(hidden=True):
			if name in kwargs:
				params[name] = kwargs.pop(name)
				# setattr(self, name, kwargs.pop(name))
		return params, kwargs


	@agnostic
	def get_hparam(self, key, default: Optional[Any] = unspecified_argument):
		val = inspect.getattr_static(self, key, unspecified_argument)
		if val is unspecified_argument:
			if default is unspecified_argument:
				raise AttributeError(f'{self} has no quirk {key!r}')
			return default
		return val


	@agnostic
	def named_quirks(self, *, hidden=False): # N-O
		owner = self if isinstance(self, type) else type(self)
		items = list(owner.__dict__.items())
		for key, val in reversed(items):
			if isinstance(val, AbstractQuirk) and (hidden or (isinstance(val, HiddenQuirk) and val.hidden(self))):
				yield key, val



class InheritableQuirky(AbstractQuirky):
	_my_inherited_quirks = None
	def __init_subclass__(cls, skip_inheritable_quirks=False, **kwargs):
		super().__init_subclass__(**kwargs)
		cls._my_inherited_quirks = []
		if not skip_inheritable_quirks:
			todo = [name for base in cls.__bases__ if issubclass(base, Quirky)
			        for name, param in base.named_quirks(hidden=True)
			        if isinstance(param, InheritableQuirk) and param.inherit(cls)]
			cls.inherit_quirks(*todo)


	@agnostic
	def named_quirks(self, *, hidden=False):
		yield from self._inherited_named_quirks(hidden=hidden)
		yield from super().named_quirks(hidden=hidden)


	@agnostic
	def inherit_quirks(self, *names: str) -> Union['InheritableQuirky', Type['InheritableQuirky']]: # TODO: return Self
		existing = set(self.quirk_names(hidden=True))
		self._my_inherited_quirks.extend(name for name in names if name not in existing)
		return self


	@agnostic
	def _inherited_named_quirks(self, *, hidden=False):
		if self._my_inherited_quirks is not None:
			for key in self._my_inherited_quirks:
				val = inspect.getattr_static(self, key, None)
				if isinstance(val, AbstractQuirk) and (hidden or (isinstance(val, HiddenQuirk) and val.hidden(self))):
					yield key, val



class Capable(InheritableQuirky, Quirky):
	pass
















