import inspect

import logging
from collections import OrderedDict
from omnibelt import split_dict, unspecified_argument, agnosticmethod, classdescriptor, ClassDescriptable, OrderedSet

from . import spaces

# prt = get_printer(__file__, format='%(levelname)s: %(msg)s')

# prt = logging.Logger('Hyperparameters')
# ch = logging.StreamHandler()
# ch.setFormatter(logging.Formatter('%(levelname)s: %(msg)s'))
# ch.setLevel(0)
# prt.addHandler(ch)



class Hyperparameter(property, classdescriptor):
	def __init__(self, name=None, fget=None, default=unspecified_argument, required=None,
	             strict=None, cache=None, fixed=None, space=None, ref=None, **kwargs):
		if ref is not None:
			if name is None:
				name = ref.name
			if fget is None:
				fget = ref.fget
			if default is unspecified_argument:
				default = ref.default_profile
			if required is None:
				required = ref.required
			if strict is None:
				strict = ref.strict
			if cache is None:
				cache = ref.cache
			if fixed is None:
				fixed = ref.fixed
			if space is None:
				space = ref.space
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
	_registered_hparams = None
	
	
	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		cls._registered_hparams = OrderedSet()
	
	
	def __init__(self, *args, **kwargs):
		self._registered_hparams = self._registered_hparams.copy()
		super().__init__(*args, **self._extract_hparams(kwargs))

	
	def _extract_hparams(self, kwargs):
		found, remaining = split_dict(kwargs, self._registered_hparams)
		for key, val in found.items():
			setattr(self, key, val)
		return remaining


	Hyperparameter = Hyperparameter
	
	
	@agnosticmethod
	def register_hparam(self, name=None, fget=None, default=unspecified_argument, ref=None, **kwargs):
		if ref is not None and name is None:
			name = ref.name
		assert name is not None
		self._registered_hparams.add(name)
		return self.Hyperparameter(fget=fget, default=default, name=name, **kwargs)
	
	
	RequiredHyperparameter = Hyperparameter.MissingHyperparameter
	
	
	@agnosticmethod
	def reset_hparams(self):
		for key, param in self.named_hyperparameters():
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
		done = set()
		for key in self._registered_hparams:
			val = inspect.getattr_static(self, key, unspecified_argument)
			if key not in done and isinstance(val, Hyperparameter):
				done.add(key)
				yield (key, val)
	
	
	@agnosticmethod
	def inherit_hparams(self, *names):
		self._registered_hparams.update(names)




# class Machine(Parametrized):
# 	pass


# class ModuleParametrized(Parametrized):


class MachineParametrized(Parametrized):
	_registered_machines = None


	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		cls._registered_machines = OrderedSet()


	def __init__(self, *args, **kwargs):
		if self._registered_machines is None:
			self._registered_machines = OrderedSet()
		self._registered_machines = self._registered_machines.copy()
		super().__init__(*args, **self._extract_machines(kwargs))

		
	def _extract_machines(self, kwargs):
		found, remaining = split_dict(kwargs, self._registered_machines)
		for key, val in found.items():
			setattr(self, key, val)
		return remaining
	
	
	@agnosticmethod
	def register_machine(self, name=None, fget=None, default=unspecified_argument, ref=None, **kwargs):
		if ref is not None and name is None:
			name = ref.name
		assert name is not None
		self._registered_machines.add(name)
		return self.Machine(fget=fget, default=default, name=name, **kwargs)
	
	
	@agnosticmethod
	def machines(self):
		for key, val in self.named_machines():
			yield val
	
	
	@agnosticmethod
	def named_machines(self):
		done = set()
		for key in self._registered_machines:
			val = inspect.getattr_static(self, key, unspecified_argument)
			if key not in done and isinstance(val, MachineParametrized.Machine):
				done.add(key)
				yield (key, val)
	
	
	@agnosticmethod
	def inherit_machines(self, *names):
		self._registered_machines.update(names)
	
	
	class Machine(Parametrized.Hyperparameter):
		def __init__(self, default=unspecified_argument, required=True, module=None, cache=None, ref=None, **kwargs):
			if ref is not None and module is None:
				module = ref.module
			if cache is None:
				cache = module is not None
			super().__init__(default=default, required=required, cache=cache, ref=ref, **kwargs)
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
	
	_inherit_fn_name = 'inherit_hparams'

	def __call__(self, cls):
		try:
			inherit_fn = getattr(cls, self._inherit_fn_name)
		except AttributeError:
			raise self.OwnerNotParametrized(f'{cls} must be a subclass of {Parametrized}')
		else:
			inherit_fn(*self.names, **self.kwargs)
		return cls



class inherit_machines:
	_inherit_fn_name = 'inherit_machines'



class hparam:
	def __init__(self, default=unspecified_argument, space=None, name=None, ref=None, **kwargs):
		self.default = default
		assert name is None, 'Cannot specify a different name with hparam'
		self.name = None
		self.space = space
		self.kwargs = kwargs
		self.ref = ref
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

	_registration_fn_name = 'register_hparam'

	def __set_name__(self, obj, name):
		if self.default is not unspecified_argument:
			self.kwargs['default'] = self.default
		self.kwargs['space'] = self.space
		self.kwargs['fget'] = getattr(self, 'fget', None)
		self.kwargs['fset'] = getattr(self, 'fset', None)
		self.kwargs['fdel'] = getattr(self, 'fdel', None)
		self.kwargs['ref'] = self.ref
		self.name = name
		try:
			reg_fn = getattr(obj, self._registration_fn_name)
		except AttributeError:
			raise self.OwnerNotParametrized(f'{obj} must be a subclass of {Parametrized}')
		else:
			setattr(obj, name, reg_fn(name, **self.kwargs))



class machine(hparam):
	_registration_fn_name = 'register_machine'
	# def __init__(self, module, **kwargs):
	# 	super().__init__(module=module, **kwargs)

