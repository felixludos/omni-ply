from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

from collections import OrderedDict
from omnibelt import get_printer, unspecified_argument

from .. import util
from ..structure import Metric, Sampler, Generator
from ..tools.kits import CraftyKit

from .abstract import AbstractDataRouter, AbstractDataSource, AbstractBatchable, AbstractCountableData, AbstractContext
from .errors import UnknownSize


prt = get_printer(__file__)



class DataCollection(CraftyKit, AbstractBatchable, AbstractDataRouter):
	_BufferTable = OrderedDict

	def __init__(self, *, buffer_table=None, **kwargs):
		if buffer_table is None:
			buffer_table = self._BufferTable()
		super().__init__(**kwargs)
		self._buffers = buffer_table


	def __len__(self):
		return len(self._tools)

	
	def named_buffers(self) -> Iterator[Tuple[str, 'AbstractDataSource']]:
		for name in reversed(self._buffers):
			yield name, self.get_buffer(name)


	def get_buffer(self, name, default=unspecified_argument) -> 'AbstractDataSource':
		buffer = self._buffers.get(name, None)
		if name in self._buffers:
			if isinstance(buffer, str):
				return self.get_buffer(buffer, default=default) # TODO: check for circular references
			return buffer
		if default is not unspecified_argument:
			return default
		raise self._MissingBuffer(name)

	
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


	def vendors(self, gizmo: str):
		if gizmo in self._buffers:
			yield from self._buffers[gizmo].vendors(gizmo)
		yield from super().vendors(gizmo)

	
	def remove_buffer(self, gizmo: str):
		if gizmo in self._buffers:
			self._buffers.remove(gizmo)


	def register_buffer(self, gizmo: str, buffer: AbstractDataSource):
		if not isinstance(buffer, AbstractDataSource):
			prt.warning(f'Expected buffer for {gizmo} in {self}, got: {buffer!r}')
		self._buffers[gizmo] = buffer
		if gizmo in self._spaces:
			self._spaces.remove(gizmo)
		return buffer


	def rename_buffer(self, current: str, new: str):
		buffer = self.get_buffer(current, None)
		if buffer is not None:
			self.remove_buffer(current)
		self.register_buffer(new, buffer)



class CountableDataRouter(AbstractDataRouter, AbstractDataSource, AbstractCountableData):
	@property
	def size(self):
		return self._compute_size() if self.is_ready else self._expected_size()


	_UnknownSize = UnknownSize
	def _compute_size(self):
		for tool in self.tools():
			if isinstance(tool, AbstractCountableData):
				return tool.size
		raise self._UnknownSize()


	def _expected_size(self): # should be implemented by subclasses
		raise self._UnknownSize()



class BranchedDataRouter(DataCollection):
	def register_buffer(self, name, buffer=None, *, space=None, **kwargs): # TODO: with delimiter for name
		raise NotImplementedError



class AutoCollection(DataCollection):
	_Buffer = None
	
	def register_buffer(self, name, buffer=None, *, space=None, **kwargs):
		if buffer is None:
			buffer = self._Buffer(space=space, **kwargs)
		elif not isinstance(buffer, AbstractDataSource):
			buffer = self._Buffer(buffer, space=space, **kwargs)
		return super().register_buffer(name, buffer)



class AliasedCollection(DataCollection):
	def register_buffer_alias(self, name: str, *aliases: str):
		'''
		Registers aliases for a buffer.

		Args:
			name: original name of the buffer
			*aliases: all the new aliases

		Returns:

		'''
		for alias in aliases:
			self._tools[alias] = name


	def has_gizmo(self, gizmo: str):
		alias = self._tools[gizmo]
		return super().has_gizmo(gizmo) and (not isinstance(alias, str) or self.has_gizmo(alias))



class Observation(AbstractDataRouter): # SampleSource
	@property
	def din(self):
		return self.observation_space
	@property
	def observation_space(self):
		return self.space_of('observation')



class Supervised(Observation, Metric):
	@property
	def dout(self):
		return self.target_space
	@property
	def target_space(self):
		return self.space_of('target')


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



class Synthetic(Labeled):#, alias={'label': 'mechanism'}): # TODO: include auto alias
	_distinct_mechanisms = True


	@property
	def mechanism_space(self):
		return self.space_of('mechanism')


	def transform_to_mechanisms(self, data):
		if not self._distinct_mechanisms:
			return data
		return self.mechanism_space.transform(data, self.label_space)


	def transform_to_labels(self, data):
		if not self._distinct_mechanisms:
			return data
		return self.label_space.transform(data, self.mechanism_space)









