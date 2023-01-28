from typing import Type, Callable, Any, Union
import torch
from omnibelt import agnosticproperty

from .abstract import AbstractContext
from .base import RawCraft, GetterTool, GetterRawCraft
from .spaced import SpatialRawCraft
from .errors import ToolFailedError



class MaterialBase(GetterTool):
	@endpoint.get_from_size
	@endpoint.get_from_indices
	@endpoint.get_next_sample
	@endpoint.get_sample_from_index
	def send_get_from(self, instance: Any, ctx: AbstractContext, gizmo: str) -> Any:
		getter_type = self._data['method']
		if getter_type not in {'get_from_size', 'get_from_indices', 'get_next_sample', 'get_sample_from_index'}:
			raise ToolFailedError(f'Unknown getter type: {getter_type}')

		fn = getattr(instance, self._data['name'])

		if getter_type == 'get_next_sample' and hasattr(ctx, 'size'):
			return self.collect_samples(fn, ctx)
		if getter_type == 'get_sample_from_index' and hasattr(ctx, 'indices'):
			return self.collect_batch(fn, ctx)

		getter = getattr(self, getter_type)
		return getter(fn, ctx)


	@staticmethod
	def collect_samples(fn: Callable, ctx: AbstractContext) -> Any:
		return torch.stack([fn() for _ in range(getattr(ctx, 'size', ctx))])


	@staticmethod
	def collect_batch(fn: Callable, ctx: AbstractContext) -> Any:
		return torch.stack([fn(index) for index in getattr(ctx, 'indices', ctx)])


	@staticmethod
	def get_from_size(fn: Callable, ctx: Union[AbstractContext, int]) -> Any:
		return fn(getattr(ctx, 'size', ctx))


	@staticmethod
	def get_from_indices(fn: Callable, ctx: AbstractContext) -> Any:
		return fn(getattr(ctx, 'indices', ctx))


	@staticmethod
	def get_next_sample(fn: Callable, ctx: AbstractContext = None) -> Any:
		return fn()


	@staticmethod
	def get_sample_from_index(fn: Callable, ctx: AbstractContext) -> Any:
		return fn(getattr(ctx, 'index', ctx))



class Material(MaterialBase):
	pass



class material(SpatialRawCraft, GetterRawCraft):
	_CraftItem = Material


	@agnosticproperty
	def get_from_size(self):
		return self._agnostic_propagator('get_from_size')


	@agnosticproperty
	def get_from_indices(self):
		return self._agnostic_propagator('get_from_indices')


	@agnosticproperty
	def get_next_sample(self):
		return self._agnostic_propagator('get_next_sample')


	@agnosticproperty
	def get_sample_from_index(self):
		return self._agnostic_propagator('get_sample_from_index')
































