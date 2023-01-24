from typing import Type, Callable, Any, Union
import torch

from .abstract import AbstractContext
from .base import RawCraft, CraftTool



class MaterialBase(CraftTool):
	def _find_getter_type(self, ctx: AbstractContext, gizmo: str) -> str:
		raise NotImplementedError # TODO


	def send_get_from(self, instance: Any, ctx: AbstractContext, gizmo: str) -> Any:
		getter_fn = self._find_getter_fn(instance, gizmo)
		getter_type = self._find_getter_type(ctx, gizmo)
		return getattr(self, getter_type)(getter_fn, ctx)


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



class material(RawCraft):
	_CraftItem = Material




































