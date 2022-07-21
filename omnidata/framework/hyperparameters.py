import inspect

import logging
from omnibelt import unspecified_argument, agnosticmethod, classdescriptor, ClassDescriptable

from . import spaces

# prt = get_printer(__file__, format='%(levelname)s: %(msg)s')

prt = logging.Logger('Hyperparameters')
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(levelname)s: %(msg)s'))
ch.setLevel(0)
prt.addHandler(ch)



class Hyperparameter(property, classdescriptor):
	def __init__(self, name=None, fget=None, default=unspecified_argument, required=False,
	             strict=False, cache=False, fixed=False, space=None, **kwargs):
		super().__init__(fget=fget, **kwargs)
		if name is None:
			assert fget is not None, 'No name provided'
			name = fget.__name__
		self.name = name
		self.cls_value = self._missing
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
			self.cls_value = self._missing
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
		elif self.cls_value is not self._missing:
			return self.cls_value
		elif self.fget is not None:
			value = self._custom_getter(cls, cls) # "class property"
			if self.cache:
				self.cls_value = value
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
			self.cls_value = value
		else:
			if self.fset is not None: # use user-defined setter
				return super().__set__(obj, value)
			obj.__dict__[self.name] = value
		return value



class Parametrized(metaclass=ClassDescriptable):
	_inherited_hparams = set()

	def __init__(self, *args, **kwargs):
		self._inherited_hparams = self._inherited_hparams.copy()
		super().__init__(*args, **self._extract_hparams(kwargs))


	def _extract_hparams(self, kwargs):
		for key, val in self.iterate_hparams(items=True):
			if key in kwargs:
				setattr(self, key, kwargs[key])
				del kwargs[key]
		for key, val in self.__class__.iterate_hparams(items=True):
			if key in kwargs:
				setattr(self, key, kwargs[key])
				del kwargs[key]
		return kwargs
	# id(newval), id(val), id(inspect.getattr_static(self, 'encoder')), id(inspect.getattr_static(self.__class__, 'encoder'))


	Hyperparameter = Hyperparameter
	@agnosticmethod
	def register_hparam(self, name=None, fget=None, default=unspecified_argument, required=False, **kwargs):
		return self.Hyperparameter(fget=fget, required=required, default=default, name=name, **kwargs)


	RequiredHyperparameter = Hyperparameter.MissingHyperparameter


	@agnosticmethod
	def reset_hparams(self):
		for key, param in self.iterate_hparams(True):
			param.reset()


	@agnosticmethod
	def iterate_hparams(self, items=False, **kwargs):
		cls = self if isinstance(self, type) else self.__class__
		done = set()
		for key, val in cls.__dict__.items():
			if key not in done and isinstance(val, Hyperparameter):
				done.add(key)
				yield (key, val) if items else key
		for key in self._inherited_hparams:
			# val = getattr(self, key, unspecified_argument) if getvalue else
			val = inspect.getattr_static(self, key, unspecified_argument)
			# val = getattr(self, key, None)
			if key not in done and isinstance(val, Hyperparameter):
				done.add(key)
				yield (key, val) if items else key

		# if not isinstance(self, type):
		# 	yield from self.__class__.iterate_hparams(items=items, **kwargs)


	@agnosticmethod
	def inherit_hparams(self, *names):
		self._inherited_hparams.update(names)
		# for name in names:
		# 	hparam = inspect.getattr_static(self, name, unspecified_argument)
		# 	if hparam is unspecified_argument:
		# 		if strict:
		# 			raise self.Hyperparameter.MissingHyperparameter(name)
		# 	else:
		# 		if copy:
		# 			hparam = hparam.copy()
		# 		self.__dict__[name] = hparam
				# setattr(self, name, hparam)



class ModuleParametrized(Parametrized):
	class Hyperparameter(Parametrized.Hyperparameter):
		def __init__(self, default=unspecified_argument, required=True, module=None, cache=None, **kwargs):
			if cache is None:
				cache = module is not None
			super().__init__(default=default, required=required, cache=cache, **kwargs)
			self.module = module


		class InvalidInstance(Hyperparameter.InvalidValue):
			def __init__(self, name, value, base, msg=None):
				if msg is None:
					value = type(value) if isinstance(value, type) else str(value)
					msg = f'{name}: {value} (expecting an instance of {base})'
				super().__init__(name, value, msg=msg)
				self.base = base


		def validate_value(self, value):
			if self.module is not None and not isinstance(value, self.module):
				raise self.InvalidInstance(self.name, value, self.module)



class inherit_hparams:
	def __init__(self, *names, **kwargs):
		self.names = names
		self.kwargs = kwargs


	class OwnerNotParametrized(Exception):
		pass


	def __call__(self, cls):
		try:
			inherit_fn = cls.inherit_hparams
		except AttributeError:
			raise self.OwnerNotParametrized(f'{cls} must be a subclass of {Parametrized}')
		else:
			inherit_fn(*self.names, **self.kwargs)
		return cls



class hparam:
	def __init__(self, default=unspecified_argument, space=None, name=None, **kwargs):
		self.default = default
		assert name is None, 'Cannot specify a different name with hparam'
		self.name = None
		self.space = space
		self.kwargs = kwargs
		self.fget = None
		self.fset = None
		self.fdel = None


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


	def __set_name__(self, obj, name):
		if self.default is not unspecified_argument:
			self.kwargs['default'] = self.default
		self.kwargs['space'] = self.space
		self.kwargs['fget'] = getattr(self, 'fget', None)
		self.kwargs['fset'] = getattr(self, 'fset', None)
		self.kwargs['fdel'] = getattr(self, 'fdel', None)
		self.name = name
		try:
			reg_fn = obj.register_hparam
		except AttributeError:
			raise self.OwnerNotParametrized(f'{obj} must be a subclass of {Parametrized}')
		else:
			setattr(obj, name, reg_fn(name, **self.kwargs))





