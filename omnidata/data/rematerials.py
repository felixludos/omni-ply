from typing import Type, Union, Any, Optional, Callable, Sequence, Iterable, Iterator, Tuple, List, Dict, NamedTuple
from collections import OrderedDict
from functools import cached_property
from omnibelt import smartproperty
from omnibelt.tricks import nested_method_decorator

from .abstract import AbstractDataSource
from .routers import DataCollection
from .sources import SpacedSource




class material_base(nested_method_decorator):
	_bindings_table = OrderedDict

	def __init__(self, *keys, replaces=None, **info):
		fn = None
		if len(keys) and callable(keys[0]): # if callable, assume it is the init function
			fn, keys = keys

		super().__init__(fn=fn)

		self.keys = keys
		self.replaces = replaces
		self.info = info
		self.bindings = self._bindings_table()

	def _setup(self, owner: Type, name: str) -> None:
		super()._setup(owner, name)
		self.name = name

	class _collector:
		class _collect_fn:
			def __init__(self, owner):
				self.owner = owner
			def __call__(self, fn):
				self.owner.fn = fn
				return fn

		def __init__(self):
			self.args = None
			self.kwargs = None
			self.fn = None

		def __call__(self, *args, **kwargs):
			self.args = args
			self.kwargs = kwargs
			return self._collect_fn(self)


	@property
	def get(self): # (src) -> data
		collector = self._collector()
		self.bindings['get'] = collector
		return collector

	@property
	def get_key(self): # (src, key) -> data
		collector = self._collector()
		self.bindings['get_key'] = collector
		return collector

	@property
	def get_from_size(self): # (N) -> data
		collector = self._collector()
		self.bindings['get_from_size'] = collector
		return collector

	@property
	def get_sample(self): # () -> data
		collector = self._collector()
		self.bindings['get_sample'] = collector
		return collector

	@property
	def transformation(self): # (**materials) -> data
		collector = self._collector()
		self.bindings['transformation'] = collector
		return collector

	@property
	def prepare(self): # () -> None
		collector = self._collector()
		self.bindings['prepare'] = collector
		return collector



class countable_material(material_base):
	@property
	def get_from_indices(self):  # (indices) -> data
		collector = self._collector()
		self.bindings['get_from_indices'] = collector
		return collector

	@property  # (idx) -> data
	def get_sample_from_index(self):
		collector = self._collector()
		self.bindings['get_sample_from_index'] = collector
		return collector



class space_material(material_base):
	@property
	def space(self):  # attribute
		collector = self._collector()
		self.bindings['space'] = collector
		return collector



class material(countable_material, space_material):
	pass



class AbstractMaterial(AbstractDataSource):
	def __init__(self, owner, mat, **kwargs):
		super().__init__(**kwargs)

	def register_with(self, collection: Type['Materialed'], mat: material_base):
		raise NotImplementedError

	def materialize(self, obj: 'Materialed'):
		raise NotImplementedError



class MaterialSource(SpacedSource, AbstractMaterial):
	@classmethod
	def register_with(cls, owner: Type['Materialed'], mat: material_base):
		cls._fix_bindings(owner, mat)
		keys = list(cls._resolve_keys(mat))
		if len(keys):
			owner._register_auto_material(mat)
			# owner._register_auto_material(mat, *keys)
		else:
			raise ValueError(f'No keys provided for material {mat} of {owner}')

	@classmethod
	def inherit_materials(cls, owner):
		for base in cls.__bases__:
			if issubclass(base, Materialed) and base._auto_materials is not None:
				yield from base._auto_materials

	@staticmethod
	def _collected_attributes():
		return {'space'}

	@classmethod
	def _fix_bindings(cls, owner, mat):
		# setattr(owner, mat.name, cls(owner, mat))
		attrs = cls._collected_attributes()
		for k, v in mat.bindings.items():
			if v is None or v.fn is None:
				continue
			# if v.fn is None:
			# 	raise ValueError(f'No function provided for binding {k} of material {self._mat} of {owner}')
			setattr(owner, v.fn.__name__, cached_property(v.fn) if k in attrs else v.fn) # TODO: property setter and deleter

	@staticmethod
	def _resolve_keys(mat):
		if mat.replaces is not None:
			yield mat.replaces
		yield from mat.keys
		if (mat.replaces is None and not len(mat.keys)) and mat.fn is not None:
			yield mat.fn.__name__

	@classmethod
	def materialize(cls, obj: 'Materialed', base: material_base):
		mat = cls(obj, base) if base.fn is None else base.fn.__get__(obj, type(obj))()
		return obj.register_material(mat, *cls._resolve_keys(base))

	def __init__(self, obj, mat, **kwargs):
		super().__init__(obj, mat, **kwargs)
		self._obj = obj
		self._base = mat

		for k in self._resolve_keys(self._mat):
			obj.register_material(k, self)

		if self._mat.bindings['prepare'].fn is not None:


	def _prepare(self, **kwargs):
		pass # TODO


	def _get_from(self, source, key=None):
		return self.fget(source, key) if self.include_key else self.fget(source)



class Materialed(DataCollection):
	_auto_materials = None
	_auto_material_table = list
	def __init_subclass__(cls, inherit_materials=None, **kwargs):
		super().__init_subclass__(**kwargs)
		table = cls._auto_material_table()
		table.extend(cls._inherited_auto_materials())
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

	@classmethod
	def _inherited_auto_materials(cls):
		for base in cls.__bases__:
			if issubclass(base, Materialed) and base._auto_materials is not None:
				yield from base._auto_materials
			# 	yield from base._inherited_auto_materials()
			# if cls._auto_materials is not None:
			# 	yield from cls._auto_materials

	Material = MaterialSource
	def _register_auto_material(self, *names, **kwargs):
		mat = self.Material(self, **kwargs)
		for name in names:
			self.register_material(name, mat)
		return mat

























































