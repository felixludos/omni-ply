from typing import Type, Union, Any, Optional, Callable, Sequence, Iterable, Iterator, Tuple, List, Dict, NamedTuple
from collections import OrderedDict
from functools import cached_property
from omnibelt import smartproperty, unspecified_argument, method_propagator
from omnibelt.tricks import nested_method_decorator

from .abstract import AbstractDataSource
from .routers import DataCollection
from .sources import SpacedSource



class material_base(method_propagator):
	@property
	def get(self): # (src) -> data
		return self._make_collector('get')


	@property
	def get_key(self): # (src, key) -> data
		return self._make_collector('get_key')


	@property
	def get_from_size(self): # (N) -> data
		return self._make_collector('get_from_size')


	@property
	def get_sample(self): # () -> data
		return self._make_collector('get_sample')


	@property
	def transformation(self): # (**materials) -> data
		return self._make_collector('transformation')


	@property
	def prepare(self): # () -> None
		return self._make_collector('prepare')



class countable_material(material_base):
	@property
	def get_from_indices(self):  # (indices) -> data
		return self._make_collector('get_from_indices')


	@property  # (idx) -> data
	def get_sample_from_index(self):
		return self._make_collector('get_sample_from_index')



class space_material(material_base):
	@property
	def space(self):  # attribute
		return self._make_collector('space')



class material(countable_material, space_material):
	pass



class AbstractMaterialTracker(AbstractDataSource):
	def __init__(self, owner, mat, **kwargs):
		super().__init__(**kwargs)



class AbstractMaterial(AbstractDataSource):
	def __init__(self, source, mat, **kwargs):
		super().__init__(**kwargs)


	@staticmethod
	def register_with(collection: Type['Materialed'], mat: material_base):
		raise NotImplementedError


	@staticmethod
	def inherit_materials(owner: Type['Materialed']):
		raise NotImplementedError


	def materialize(self, collection: 'Materialed', base: material_base, **kwargs):
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


	@staticmethod
	def _process_base():



		pass


	@classmethod
	def inherit_materials(cls, owner: Type['Materialed']):
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
		if (mat.replaces is None and not len(mat.keys)) and mat._fn is not None:
			yield mat._fn.__name__


	@classmethod
	def materialize(cls, collection: 'Materialed', base: material_base, *, mat=None, **kwargs):
		# if data is None and base.fn is not None:
		# 	data = cls._call_source_fn(collection, base.fn)
		if mat is None:
			mat = cls(collection, base, **kwargs) if base._fn is None else cls(collection, base, **kwargs)
		for name in cls._resolve_keys(base):
			collection.register_material(name, mat)


	def __init__(self, source: 'Materialed', mat: material_base, *, space=None, **kwargs):
		if space is None:
			space = mat.info.get('space', None)
		super().__init__(source, mat, space=space, **kwargs)
		self._source = source
		self._base = mat


	def _extract_base_attrs(self):
		if 'space' in self._base.bindings:
			self._space = self._call_source_fn(self._source, self._base.bindings['space'].fn)


	def _prepare(self, *args, **kwargs):
		if 'prepare' in self._base.bindings:
			self._call_source_fn(self._source, self._base.bindings['prepare'].fn, *args, **kwargs)


	@staticmethod
	def _call_source_fn(source: 'Materialed', fn: Callable, *args, **kwargs):
		return getattr(source, fn.__name__)(*args, **kwargs)


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

























































