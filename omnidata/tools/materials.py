from typing import Type, Callable, Any, Union
import torch

from .abstract import AbstractContext
from .base import RawCraft, CraftTool
from .spaced import SpatialRawCraft



class MaterialBase(CraftTool):
	def send_get_from(self, instance: Any, ctx: AbstractContext, gizmo: str) -> Any:
		fn = getattr(instance, self._data['name'])
		getter = getattr(self, self._data['method'])
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



class material(SpatialRawCraft):
	_CraftItem = Material




































