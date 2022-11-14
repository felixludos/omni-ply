
from omnibelt import smartproperty

from .abstract import AbstractDataSource, AbstractView
from .routers import DataCollection
from .sources import SpacedSource


class material(smartproperty):
	def __init__(self, *names, space=None, fget=None, **kwargs):
		if len(names) == 1 and callable(names[0]):
			fget = names[0]
			names = ()
		super().__init__(fget=fget)
		# super().__init__(fget=fget, **kwargs)
		self.names = names
		self.space = space
		self.kwargs = kwargs


	def _get_registration_args(self, obj):
		info = self.kwargs.copy()
		info['space'] = self.space
		info['fget'] = self.fget
		return info


	_registration_fn_name = '_register_auto_material'
	_default_base = None

	def register_with(self, obj, name):
		names = self.names if len(self.names) else (name,)
		reg_fn = getattr(obj, self._registration_fn_name)
		kwargs = self._get_registration_args(obj)
		if 'include_key' not in kwargs:
			kwargs['include_key'] = True
		if reg_fn is None:
			assert len(names) == 1, 'Cannot register multiple names without a registration function'
			if self._default_base is None:
				raise ValueError(f'No registration function found on {obj} and no default base set')
			name = names[0]
			value = self._default_base(name, **kwargs)
			setattr(obj, name, value)
		else:
			reg_fn(*names, **kwargs)



class MaterialSource(SpacedSource, AbstractDataSource):
	def __init__(self, source, *, fget=None, include_key=False, **kwargs):
		super().__init__(**kwargs)
		self.include_key = include_key
		self.fget = fget
		self.getter = self.fget.__get__(source, source.__class__)

	def _get_from(self, source, key):
		return self.getter(source, key) if self.include_key else self.getter(source)



class Materialed(DataCollection):
	def __init__(self, _skip_auto_registration=False, **kwargs):
		super().__init__(**kwargs)
		if not _skip_auto_registration:
			for key, val in self.__class__.__dict__.items():
				if isinstance(val, material):
					val.register_with(self, key)


	Material = MaterialSource
	def _register_auto_material(self, *names, **kwargs):
		mat = self.Material(self, **kwargs)
		for name in names:
			self.register_material(name, mat)
		return mat



# class Process(Materialed):
#
# 	@material('observation', space=None)
# 	def _observation(self, source, key):
# 		return [1,2,3]






