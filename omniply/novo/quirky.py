from .imports import *

from .quirks import *


class Quirky:
	def fill_quirks(self, fn, args=None, kwargs=None, **finder_kwargs) -> Dict[str, Any]:
		raise NotImplementedError


	def _extract_quirks(self, kwargs):
		raise NotImplementedError


	# def _existing_quirks(self, *, hidden=False):
	# 	for key, param in self.named_quirks(hidden=hidden):
	# 		if param.is_missing(self):
	# 			yield key, getattr(self, key)


	def has_quirk(self, key):
		raise NotImplementedError


	def get_quirk(self, key, default=unspecified_argument):
		raise NotImplementedError


	@classmethod
	def quirks(cls, *, hidden=False):
		for key, val in cls.named_quirks(hidden=hidden):
			yield val


	@classmethod
	def named_quirks(cls, *, hidden=False):
		raise NotImplementedError


	@classmethod
	def quirk_names(cls, *, hidden=False):
		for key, val in cls.named_quirks(hidden=hidden):
			yield key


	@classmethod
	def inherit_quirks(cls, *names):
		raise NotImplementedError



class Capable(Quirky):
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


	@classmethod
	def get_hparam(cls, key, default: Optional[Any] = unspecified_argument):
		# val = inspect.getattr_static(self, key, unspecified_argument)
		val = getattr(cls, key, unspecified_argument)
		if val is unspecified_argument:
			if default is unspecified_argument:
				raise AttributeError(f'{cls.__name__} has no hyperparameter {key}')
			return default
		return val


	def has_quirk(self, key):
		return isinstance(self.get_hparam(key, None), AbstractQuirk)


	@classmethod
	def named_quirks(cls, *, hidden=False):
		items = list(cls.__dict__.items())
		for key, val in reversed(items):
			if isinstance(val, AbstractQuirk) and (hidden or not getattr(val, 'hidden', False)):
				yield key, val


















