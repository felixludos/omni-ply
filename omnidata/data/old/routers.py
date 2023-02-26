from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

from collections import OrderedDict
from omnibelt import get_printer, unspecified_argument

from .. import util
from ..structure import Metric, Sampler, Generator
from .abstract import AbstractDataRouter, AbstractDataSource, AbstractBatchable, AbstractCountableData
from .sources import SpacedSource, SampleSource


prt = get_printer(__file__)


# class ExpectingDataRouter(AbstractDataRouter): # TODO: future feature
# 	def __init_subclass__(cls, materials=None, required_materials=None, **kwargs):
# 		super().__init_subclass__(**kwargs)
# 		if required_materials is not None:
# 			raise NotImplementedError
# 		if isinstance(materials, str):
# 			materials = [materials]
# 		base = getattr(cls, '_expecting_materials', [])
# 		cls._expecting_materials = base + (materials or [])
#
#
# 	def _prepare(self, source=None, **kwargs):
# 		super()._prepare(source=source, **kwargs)
# 		for material in self._expecting_materials:
# 			if not self.has(material):
# 				prt.warning(f'Expected material {material!r} not found in {self}')



class DataCollection(AbstractBatchable, AbstractDataRouter):
	def __init__(self, *, materials_table=None, **kwargs):
		if materials_table is None:
			materials_table = self._MaterialsTable()
		super().__init__(**kwargs)
		self._registered_materials = materials_table
	
	_MaterialsTable = OrderedDict


	def __len__(self):
		return len(self._registered_materials)


	def copy(self):
		new = super().copy()
		new._registered_buffers = new._registered_buffers.copy()
		return new


	def space_of(self, key):
		return self.get_material(key).space


	def _get_from(self, source, key=None):
		return self.get_material(key).get_from(source, key)
	
	
	def named_materials(self) -> Iterator[Tuple[str, 'AbstractDataSource']]:
		for name in self._registered_materials:
			yield name, self.get_material(name)


	def get_material(self, name, default=unspecified_argument):
		material = self._registered_materials.get(name, unspecified_argument)
		if isinstance(material, str):
			return self.get_material(material, default=default) # TODO: check for circular references
		if material is not unspecified_argument:
			return material
		if default is not unspecified_argument:
			return default
		raise self.MissingMaterial(name)
	
	def has(self, name):
		return name in self._registered_materials
	
	
	# def _fingerprint_data(self):
	# 	# data = super()._fingerprint_data()
	# 	# if self.is_ready:
	# 	# 	data['buffers'] = {}
	# 	# 	for name, buffer in self.iter_named_buffers():
	# 	# 		data['buffers'][name] = buffer.fingerprint()
	# 	# return data
	# 	# return {'buffers': {name:buffer.fingerprint() for name, buffer in self.iter_named_buffers()}, 'ready': self.is_ready,
	# 	#         **super()._fingerprint_data()}
	# 	raise NotImplementedError
	
	
	def remove_material(self, name):
		self._registered_materials.remove(name)
	
	def register_material(self, name, material):
		if not isinstance(material, AbstractDataSource):
			prt.warning(f'Expected material for {name} in {self}, got: {material!r}')
		self._registered_materials[name] = material
		return material
	
	def rename_material(self, current, new):
		material = self.get_material(current, None)
		if material is not None:
			self.remove_material(current)
		self.register_material(new, material)


class CountableDataRouter(AbstractDataRouter, AbstractDataSource, AbstractCountableData):
	def __init__(self, default_len=None, **kwargs):
		super().__init__(**kwargs)
		self._default_len = default_len

	class UnknownCount(TypeError):
		def __init__(self):
			super().__init__('did you forget to provide a "default_len" in __init__?')

	@property
	def size(self):
		if self.is_ready:
			return next(self.materials()).size
		if self._default_len is not None:
			return self._default_len
		raise self.UnknownCount()





class BranchedDataRouter(DataCollection):
	def register_material(self, name, material=None, *, space=None, **kwargs): # TODO: with delimiter for name
		raise NotImplementedError



class AutoCollection(DataCollection):
	Buffer = None
	
	def register_material(self, name, material=None, *, space=None, **kwargs):
		if material is None:
			material = self.Buffer(space=space, **kwargs)
		elif not isinstance(material, AbstractDataSource):
			material = self.Buffer(material, space=space, **kwargs)
		return super().register_material(name, material)



class AliasedCollection(DataCollection):
	def register_material_alias(self, name: str, *aliases: str):
		'''
		Registers aliases for a material.

		Args:
			name: original name of the material
			*aliases: all the new aliases

		Returns:

		'''
		for alias in aliases:
			self._registered_materials[alias] = name
	
	def has(self, name):
		alias = self._registered_materials[name]
		return super().has(name) and (not isinstance(alias, str) or self.has(alias))



# class CachedDataRouter(AbstractDataRouter):
# 	def cached(self) -> Iterator[str]:
# 		raise NotImplementedError
#
# 	def __str__(self):
# 		cached = set(self.cached())
# 		return f'{self._title()}(' \
# 		       f'{", ".join((key if key in cached else "{" + key + "}") for key in self.available())})'



# def __setattr__(self, key, value):
# 	if isinstance(value, AbstractCollection):
# 		self._register_multi_material(value, *value.available())
# 	if isinstance(value, AbstractMaterial):
# 		self.register_material(key, value)
# 	super().__setattr__(key, value)
#
# def __delattr__(self, name):
# 	if name in self._registered_materials:
# 		self.remove_material(name)
# 	super().__delattr__(name)




class Observation(SampleSource, AbstractDataRouter):
	_sample_key = 'observation'

	@property
	def din(self):
		return self.observation_space

	@property
	def observation_space(self):
		return self.space_of('observation')
	@observation_space.setter
	def observation_space(self, space):
		self.get_material('observation').space = space



class Supervised(Observation, Metric):
	@property
	def dout(self):
		return self.target_space


	@property
	def target_space(self):
		return self.space_of('target')
	@target_space.setter
	def target_space(self, space):
		self.get_material('target').space = space


	def difference(self, a, b, standardize=None):
		return self.dout.difference(a, b, standardize=standardize)


	def measure(self, a, b, standardize=None):
		return self.dout.measure(a, b, standardize=standardize)


	def distance(self, a, b, standardize=None):
		return self.dout.distance(a, b, standardize=standardize)



class Labeled(Supervised):#, alias={'target': 'label'}):
	@property
	def label_space(self):
		return self.space_of('label')
	@label_space.setter
	def label_space(self, space):
		self.get_material('label').space = space



class Synthetic(Labeled):#, alias={'label': 'mechanism'}): # TODO: include auto alias
	_distinct_mechanisms = True

	@property
	def mechanism_space(self):
		return self.space_of('mechanism')
	@mechanism_space.setter
	def mechanism_space(self, space):
		self.get_material('mechanism').space = space


	def transform_to_mechanisms(self, data):
		if not self._distinct_mechanisms:
			return data
		return self.mechanism_space.transform(data, self.label_space)


	def transform_to_labels(self, data):
		if not self._distinct_mechanisms:
			return data
		return self.label_space.transform(data, self.mechanism_space)









