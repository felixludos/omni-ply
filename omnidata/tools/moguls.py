from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
import math

# moguls generate contexts

from ..features import Prepared

from .abstract import AbstractMogul, AbstractContext, AbstractSourcedKit, AbstractResource, \
	AbstractTool, AbstractDynamicKit, AbstractScopable, AbstractResourceable, AbstractDynamicContext



class IterableMogul(AbstractMogul):
	def __iter__(self):
		raise NotImplementedError



class IteratorMogul(IterableMogul):
	def __iter__(self):
		return self


	def __next__(self):
		raise NotImplementedError


	def current_context(self):
		raise NotImplementedError


	def done(self) -> bool:
		'''not done guarantees that __next__ will return a new context'''
		raise NotImplementedError



class LimitMogul(IterableMogul):
	def __len__(self):
		raise NotImplementedError



class SelectionMogul(IterableMogul):
	def __getitem__(self, item):
		raise NotImplementedError



class BuildingContextMogul(AbstractMogul):
	def build_context(self) -> AbstractContext:
		raise NotImplementedError



class ValidationMogul(AbstractMogul):
	def validate_context(self, ctx: AbstractContext) -> AbstractContext:
		return ctx



########################################################################################################################



# class SimpleMogul(AbstractMogul):
# 	def __init__(self, resources=None, **kwargs):
# 		if resources is None:
# 			resources = []
# 		super().__init__(**kwargs)
# 		self._resources = resources
#
#
# 	def resources(self) -> Iterator[AbstractResource]:
# 		yield from reversed(self._resources)




class DefaultResourceMogul(AbstractMogul, AbstractDynamicKit):
	class _DefaultResource(AbstractResource):
		def __init__(self, source: AbstractTool, **kwargs):
			super().__init__(**kwargs)
			self._source = source


		@property
		def source(self) -> AbstractTool:
			return self._source


		def validate_context(self, ctx: AbstractDynamicContext) -> AbstractContext:
			return ctx.include(self.source)


	def __init__(self, *, resources=None, **kwargs):
		if resources is None:
			resources = []
		super().__init__(**kwargs)
		self._resources = resources


	def resources(self) -> Iterator[AbstractResource]:
		yield from reversed(self._resources)


	def _as_resource(self, source: AbstractTool):
		resource = source.as_resource(self) if isinstance(source, AbstractResourceable) else None
		if resource is None:
			resource = self._DefaultResource(source)
		return resource


	def include(self, *sources: AbstractTool):
		for source in sources:
			self._resources.append(self._as_resource(source))
		return self



class CreativeMogul(AbstractMogul):
	_Context = None


	def _create_context(self, *args, **kwargs):
		return self._Context(*args, **kwargs)



class ValidatedCreativeMogul(CreativeMogul, AbstractResource):
	def _validate_context(self, ctx: AbstractContext) -> AbstractContext: # as a driver or an observer
		for resource in self.resources():
			ctx = resource.validate_context(ctx)
		return ctx


	def _create_context(self, *args, **kwargs): # as a driver
		return self._validate_context(super()._create_context(*args, **kwargs))


	def validate_context(self, ctx: AbstractContext) -> AbstractContext: # as an observer
		return self._validate_context(ctx)



class SimpleMogul(DefaultResourceMogul, ValidatedCreativeMogul):
	pass



########################################################################################################################



class OptimMogul(IterableMogul):
	@property
	def iteration_count(self) -> int: # of the optimizer
		raise NotImplementedError



class OptimBudgetMogul(OptimMogul):
	@property
	def budget_iterations(self) -> Optional[int]:
		raise NotImplementedError


	@property
	def remaining_iterations(self):
		return self.budget_iterations - self.iteration_count



class BatchMogul(IterableMogul):
	@property
	def batch_size(self):
		raise NotImplementedError


	@property
	def sample_count(self) -> int:
		raise NotImplementedError
	@property
	def batch_count(self) -> int:
		raise NotImplementedError



class EpochStatMogul(BatchMogul, LimitMogul):
	@property
	def epoch_size(self):
		raise NotImplementedError


	@property
	def current_epoch(self) -> int:
		raise NotImplementedError


	@property
	def completed_epochs(self) -> int:
		raise NotImplementedError



# class BudgetMogul(BatchBudgetMogul, OptimBudgetMogul):
# 	pass



########################################################################################################################



# class SimpleTrainer(DynamicMogul):
# 	def __init__(self, model, *, optim=None, **kwargs):
# 		if optim is None:
# 			optim = model.default_optim()
# 		super().__init__(**kwargs)
# 		self.model = model
# 		self.optim = optim
#
#
# 	def fit(self, dataset):
# 		for ctx in self.iterate(dataset):
# 			out = self.step(ctx)
# 		raise NotImplementedError
# 		# return out
#
#
# 	@staticmethod
# 	def iterate(dataset):
# 		yield from dataset
#
#
# 	def step(self, ctx):
# 		self.optim.step(ctx)
#
#
#
# class Checkpoint(SimpleTrainer):
# 	def checkpoint(self, ctx):
# 		pass
#
#
#
# class Evaluatable(SimpleTrainer):
# 	def evaluate(self, dataset): # valset or testset
# 		pass






