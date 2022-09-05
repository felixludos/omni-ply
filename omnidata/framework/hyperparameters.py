import inspect

import logging
from collections import OrderedDict
from omnibelt import split_dict, unspecified_argument, agnosticmethod, OrderedSet, \
	extract_function_signature, method_wrapper

from . import spaces

# prt = get_printer(__file__, format='%(levelname)s: %(msg)s')

prt = logging.Logger('Hyperparameters')
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(levelname)s: %(msg)s'))
ch.setLevel(0)
prt.addHandler(ch)


# TODO: add property "hidden" to avoid registering certain parameters

class SimpleHyperparameter(property):
	def __init__(self, name=None, default=unspecified_argument, *, required=None, fget=None,
	             strict=None, cache=None, fixed=None, space=None, **kwargs):
		if required is None:
			required = False
		if strict is None:
			strict = False
		if cache is None:
			cache = False
		if fixed is None:
			fixed = False
		super().__init__(fget=fget, **kwargs)
		if name is None:
			assert fget is not None, 'No name provided'
			name = fget.__name__
		self.name = name
		self.cached_value = self._missing
		self.default = default
		self.cache = cache
		if space is not None and isinstance(space, (list, tuple, set)):
			space = spaces.Categorical(space)
		self.space = space
		self.required = required
		self.fixed = fixed
		self.strict = strict # raises and error if an invalid value is set


	def getter(self, fn):
		self.fget = fn
		return self


	def setter(self, fn):
		self.fset = fn
		return self


	def deleter(self, fn):
		self.fdel = fn
		return self


	def copy(self, name=unspecified_argument, fget=unspecified_argument, default=unspecified_argument,
	         required=unspecified_argument, strict=unspecified_argument, cache=unspecified_argument,
	         fixed=unspecified_argument, space=unspecified_argument, **kwargs):

		if name is unspecified_argument:
			name = self.name
		if fget is unspecified_argument:
			fget = self.fget
		if default is unspecified_argument:
			default = self.default
		if required is unspecified_argument:
			required = self.required
		if strict is unspecified_argument:
			strict = self.strict
		if cache is unspecified_argument:
			cache = self.cache
		if fixed is unspecified_argument:
			fixed = self.fixed
		if space is unspecified_argument:
			space = self.space
		copy = self.__class__(name=name, fget=fget, default=default, required=required, strict=strict, cache=cache,
		                      fixed=fixed, space=space, **kwargs)
		# copy.value = self.value
		return copy


	class _missing(Exception):
		pass


	class MissingHyperparameter(KeyError):
		pass


	class InvalidValue(Exception):
		def __init__(self, name, value, msg=None):
			if msg is None:
				msg = f'{name}: {value}'
			super().__init__(msg)
			self.name = name
			self.value = value


	def reset(self, obj=None):
		if obj is None:
			self.cached_value = self._missing
		elif self.fdel is not None:
			super().__delete__(obj)
		elif not isinstance(obj, type) and self.name in obj.__dict__:
			del obj.__dict__[self.name]


	def __str__(self):
		try:
			value = self.get_value()
			value = repr(value)
		except self.MissingHyperparameter:
			value = '?'
		return f'{self.__class__.__name__}({value})'#<{hex(id(self))[2:]}>' # TODO: testing


	def __get__(self, obj, cls=None):
		return self.get_value(obj, cls=cls)


	def __delete__(self, obj): # TODO: test this
		self.reset(obj=obj)


	def __set__(self, obj, value):
		self.update_value(value, obj=obj)
		# return self.cls_value


	def _custom_getter(self, obj, cls):
		try:
			return super().__get__(obj, cls)
		except Hyperparameter.MissingHyperparameter:
			raise self.MissingHyperparameter(self.name)


	def get_value(self, obj=None, cls=None):
		if obj is not None:
			if self.name in obj.__dict__:
				return obj.__dict__[self.name]
			if self.fget is not None:
				value = self._custom_getter(obj, cls)
				if self.cache:
					obj.__dict__[self.name] = value
				return value
		elif self.cached_value is not self._missing:
			return self.cached_value
		elif self.fget is not None:
			value = self._custom_getter(cls, cls) # "class property"
			if self.cache:
				self.cached_value = value
			return value
		if self.required or self.default is unspecified_argument:
			raise self.MissingHyperparameter(self.name)
		return self.default


	class FixedHyperparameter(Exception):
		def __init__(self, msg='cant change'):
			super().__init__(msg)


	def validate_value(self, value):
		if self.space is not None:
			try:
				self.space.validate(value)
			except self.space.InvalidValue:
				raise self.InvalidValue


	def update_value(self, value, obj=None):
		if self.fixed:
			raise self.FixedHyperparameter
		try:
			self.validate_value(value)
		except self.InvalidValue as e:
			if self.strict:
				raise e
			prt.warning(f'{type(e).__name__}: {e}')
		if isinstance(obj, type): # "updating" the class variable
			self.cached_value = value
		else:
			if self.fset is not None: # use user-defined setter
				return super().__set__(obj, value)
			obj.__dict__[self.name] = value
		return value



class Hyperparameter(SimpleHyperparameter):
	_default_init_args = {'default': unspecified_argument}

	def __init__(self, name=None, default=unspecified_argument, *, ref=None, **kwargs):
		if ref is not None:
			kwargs = self._check_ref(ref, {'name': name, 'default': default, **kwargs}, self._default_init_args)
			name = kwargs['name']
			default = kwargs['default']
		super().__init__(name=name, default=default, **kwargs)
		self.ref = ref


	def _check_ref(self, ref, kwargs, defaults):
		'''replaces any kwargs that are defaults with the ref value'''

		if ref is not None:
			fix = {}
			for k, v in kwargs.items():
				if v is defaults.get(k):
					fix[k] = getattr(ref, k)
			kwargs.update(fix)
		return kwargs



class hparam:
	def __init__(self, default=unspecified_argument, *, space=None, name=None, **kwargs):
		assert name is None, 'Cannot specify a different name with hparam'
		self.name = None
		self.space = space
		self.kwargs = kwargs
		self.fget = None
		self.fset = None
		self.fdel = None
		self.default = self._fix_default_value(default)

	def _fix_default_value(self, default=unspecified_argument):
		if callable(default) and not isinstance(default, type) and default.__qualname__ != default.__name__:
			self.fget = default
			default = unspecified_argument
		return default

	def setter(self, fn):
		self.fset = fn
		return self


	def deleter(self, fn):
		self.fdel = fn
		return self


	def __call__(self, fn):
		self.fget = fn
		return self


	def __get__(self, instance, owner): # TODO: this is just for linting, right?
		return getattr(instance, self.name)


	class OwnerNotParametrized(Exception):
		pass

	_registration_fn_name = 'register_hparam'

	def register_with(self, obj):
		reg_fn = getattr(obj, self._registration_fn_name)

		kwargs = self.kwargs.copy()
		if self.default is not unspecified_argument:
			kwargs['default'] = self.default
		kwargs['space'] = self.space
		kwargs['fget'] = getattr(self, 'fget', None)
		kwargs['fset'] = getattr(self, 'fset', None)
		kwargs['fdel'] = getattr(self, 'fdel', None)

		assert self.name is not None, 'Cannot register hparam without a name'
		reg_fn(self.name, **kwargs)

	def __set_name__(self, obj, name):
		self.name = name
		setattr(obj, name, self)
		# return self



class Parameterized:
	_registered_hparams = None
	

	def __init_subclass__(cls, skip_auto_registration=False, **kwargs):
		super().__init_subclass__(**kwargs)
		cls._registered_hparams = OrderedSet()
		if not skip_auto_registration:
			for key, val in cls.__dict__.items():
				if isinstance(val, hparam):
					val.register_with(cls)
				elif isinstance(val, SimpleHyperparameter):
					cls.register_hparam(key, val)
	
	
	def __init__(self, *args, **kwargs):
		self._registered_hparams = self._registered_hparams.copy()
		super().__init__(*args, **self._extract_hparams(kwargs))


	@agnosticmethod
	def fill_hparams(self, fn, args=(), kwargs={}):
		def defaults(n):
			if n in self._registered_hparams:
				return getattr(self, n)
			raise KeyError(n)
		return extract_function_signature(fn, args, kwargs, defaults)


	@agnosticmethod
	def _extract_hparams(self, kwargs):
		found, remaining = split_dict(kwargs, self._registered_hparams)
		for key, val in found.items():
			setattr(self, key, val)
		return remaining


	Hyperparameter = Hyperparameter
	
	
	@agnosticmethod
	def register_hparam(self, name=None, _instance=None, default=unspecified_argument, fget=None, ref=None, **kwargs):
		if _instance is None:
			if ref is not None and name is None:
				name = ref.name
			_instance = self.Hyperparameter(fget=fget, default=default, name=name, **kwargs)
		if name is None:
			name = _instance.name
		assert name is not None
		self._registered_hparams.add(name)
		setattr(self, name, _instance)
	
	
	@property
	def RequiredHyperparameterError(self):
		return self.Hyperparameter.MissingHyperparameter
	
	
	@agnosticmethod
	def reset_hparams(self):
		for param in self.hyperparameters():
			param.reset()
	

	@agnosticmethod
	def get_hparam(self, key, default=unspecified_argument):
		val = inspect.getattr_static(self, key, default)
		if default is unspecified_argument and val is default:
			raise AttributeError(f'{self.__class__.__name__} has no attribute {key}')
		return val
	
	
	@agnosticmethod
	def hyperparameters(self):
		for key, val in self.named_hyperparameters():
			yield val
	
	
	@agnosticmethod
	def named_hyperparameters(self):
		for key in self._registered_hparams:
			val = self.get_hparam(key, None)
			if isinstance(val, Hyperparameter):
				yield key, val


	@agnosticmethod
	def full_spec(self, fmt='{}', fmt_rule='{parent}.{child}'):
		for key, val in self.named_hyperparameters():
			yield fmt.format(key), val

	
	@agnosticmethod
	def inherit_hparams(self, *names, prepend=True):
		if prepend:
			for name in reversed(names):
				self._registered_hparams.discard(name)
				self._registered_hparams.insert(0, name)
		else:
			self._registered_hparams.update(names)



class inherit_hparams:
	def __init__(self, *names, **kwargs):
		self.names = names
		self.kwargs = kwargs

	class OwnerNotParametrized(Exception):
		pass

	_inherit_fn_name = 'inherit_hparams'

	def __call__(self, cls):
		try:
			inherit_fn = getattr(cls, self._inherit_fn_name)
		except AttributeError:
			raise self.OwnerNotParametrized(f'{cls} must be a subclass of {Parameterized}')
		else:
			inherit_fn(*self.names, **self.kwargs)
		return cls



class with_hparams(method_wrapper):
	def __init__(self, fn=None, *, static=False):
		super().__init__(fn)
		self.static = static


	def process_args(self, args, kwargs):
		args, kwargs = self.obj.fill_hparams(self.fn, args, kwargs)

		if not self.static:
			args = (self.obj, *args)
		return args, kwargs



