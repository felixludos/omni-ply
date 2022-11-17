from collections import OrderedDict
from omnibelt import smartproperty

from .abstract import AbstractDataSource
from .routers import DataCollection
from .sources import SpacedSource


class material:
	def __init__(self, name, *, space=None, **kwargs):
		assert isinstance(name, str), f'Expected name to be a string, got {name!r}'
		# if len(names) == 1 and callable(names[0]):
		# 	fget = names[0]
		# 	names = ()
		super().__init__(**kwargs)
		# super().__init__(fget=fget, **kwargs)
		self.name = name
		self.fget = None
		self.space = space
		self.kwargs = kwargs

	def __call__(self, fn):
		# self.fn_name = fn.__get__(None, None).__name__
		self.fget = fn
		return self

	def __get__(self, obj, cls):
		return self.fget.__get__(obj, cls)

	def _get_registration_args(self, obj):
		info = self.kwargs.copy()
		info['space'] = self.space
		# info['fget'] = self.fget.__name__
		info['fget'] = self.fget.__get__(obj, obj.__class__)
		return info


	_registration_fn_name = '_register_auto_material'
	_default_base = None

	def register_with(self, obj):
		reg_fn = getattr(obj, self._registration_fn_name)
		kwargs = self._get_registration_args(obj)

		if reg_fn is None:
			raise NotImplementedError
		reg_fn(self.name, **kwargs)
		if isinstance(self.fget, material):
			self.fget.register_with(obj)

		# if reg_fn is None:
		# 	assert len(names) == 1, 'Cannot register multiple names without a registration function'
		# 	if self._default_base is None:
		# 		raise ValueError(f'No registration function found on {obj} and no default base set')
		# 	name = names[0]
		# 	value = self._default_base(name, **kwargs)
		# 	setattr(obj, name, value)
		# else:
		# 	reg_fn(*names, **kwargs)



class MaterialSource(SpacedSource):
	def __init__(self, source, *, fget=None, include_key=False, **kwargs):
		super().__init__(**kwargs)
		self._source = source
		self.include_key = include_key
		self.fget = fget

	def _get_from(self, source, key=None):
		return self.fget(source, key) if self.include_key else self.fget(source)



class Materialed(DataCollection):
	_auto_materials = None
	_auto_material_table = list
	def __init_subclass__(cls, inherit_materials=None, **kwargs):
		super().__init_subclass__(**kwargs)
		table = cls._auto_material_table()
		prev = getattr(cls, '_auto_materials', None)
		if prev is not None:
			table.extend(prev)
		for key, val in cls.__dict__.items():
			if isinstance(val, material):
				table.append(val)
		cls._auto_materials = table

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._auto_registration()

	def _auto_registration(self):
		for mat in self._auto_materials:
			mat.register_with(self)

	Material = MaterialSource
	def _register_auto_material(self, *names, **kwargs):
		mat = self.Material(self, **kwargs)
		for name in names:
			self.register_material(name, mat)
		return mat




