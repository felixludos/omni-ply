from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
import math

# moguls generate contexts

from ..features import Prepared

from .abstract import AbstractMogul, AbstractContext, AbstractSourcedKit, AbstractResource, \
	AbstractTool, AbstractSchema, AbstractDynamicKit, AbstractScopable



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


	@property
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



# class SchemaMogul(AbstractMogul):
# 	def schemas(self) -> Iterator[AbstractSchema]:
# 		raise NotImplementedError



class ValidationMogul(AbstractMogul):
	def validate_context(self, ctx: AbstractContext) -> AbstractContext:
		return ctx



########################################################################################################################



class SimpleMogul(AbstractMogul):
	def __init__(self, resources=None, **kwargs):
		if resources is None:
			resources = []
		super().__init__(**kwargs)
		self._resources = resources


	def resources(self) -> Iterator[AbstractResource]:
		yield from reversed(self._resources)



class AbstractDynamicKit(AbstractKit):
	def add_source(self, source: AbstractTool):
		raise NotImplementedError



class DefaultResourceMogul(SimpleMogul, AbstractDynamicKit):
	class _DefaultResource(AbstractResource):
		def __init__(self, source: AbstractTool, **kwargs):
			super().__init__(**kwargs)
			self._source = source


		@property
		def source(self) -> AbstractTool:
			return self._source


		def validate_context(self, ctx: AbstractDynamicKit) -> AbstractDynamicKit:
			source = self._source.as_scope(ctx) if isinstance(self._source, AbstractSchema) else self._source
			ctx.add_source(source)
			return ctx


	def add_source(self, source: AbstractTool):
		if isinstance(source, AbstractSchema):
			source = source.as_resource(self)
		elif isinstance(source, AbstractResource):
			pass
		else:
			source = self._DefaultSchema(source)

		self._resources.append(source)

		return self



class CreativeMogul(AbstractMogul):
	_Context = None


	def _create_context(self, *args, **kwargs):
		return self._Context(*args, **kwargs)



class SchemaCreativeMogul(CreativeMogul, SchemaMogul):
	def _create_context(self, *args, **kwargs):
		ctx = super()._create_context(*args, **kwargs)
		for schema in self.schemas():
			ctx = schema.validate_context(ctx)
		return ctx



class SimpleMogul(CreativeMogul, AbstractSourcedKit):
	def __init__(self, *, sources=None, schemas=None, **kwargs):
		if sources is None:
			sources = []
		if schemas is None:
			schemas = []
		super().__init__(**kwargs)
		self._sources = sources
		self._schemas = schemas


	def sources(self) -> Iterator[AbstractTool]:
		yield from reversed(self._sources)


	def schemas(self) -> Iterator[AbstractTool]:
		yield from reversed(self._schemas)


	def validate_context(self, ctx: AbstractContext) -> AbstractContext:
		for schema in self.schemas():
			ctx = schema.validate_context(ctx)
		return ctx


	def add_source(self, *sources: AbstractTool):
		for source in sources:
			self._sources.append(source)
			schema = source.as_schema(self) if isinstance(source, AbstractResource) else None
			if schema is None:
				schema = source
			self._schemas.append(schema)
		return self


	def _create_context(self, *args, **kwargs):
		ctx = super()._create_context(*args, **kwargs)
		for schema in self.schemas():
			ctx.add_source(schema)
		return ctx



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



class BatchBudgetStatMogul(BatchMogul):
	@staticmethod
	def compute_budget(samples_per_batch, strict_batch_size=False,
	                   sample_limit=None, batch_limit=None, strict_limit=True):
		if sample_limit is None and batch_limit is None:
			return None, None  # infinite

		total_samples = None
		if batch_limit is not None:
			total_samples = batch_limit * samples_per_batch
		if sample_limit is not None:
			total = sample_limit - (sample_limit % samples_per_batch)
			remainder = sample_limit % samples_per_batch
			if remainder > 0:
				if strict_limit and not strict_batch_size:
					total += remainder
				elif not strict_limit:
					total += samples_per_batch
			if total_samples is None or total < total_samples:
				total_samples = total

		total_batches = total_samples // samples_per_batch
		remainder = total_samples % samples_per_batch
		if not strict_batch_size and remainder > 0:
			total_batches += 1

		return total_samples, total_batches


	@property
	def budget_samples(self) -> Optional[int]:
		raise NotImplementedError


	@property
	def budget_batches(self) -> Optional[int]:
		raise NotImplementedError


	@property
	def remaining_samples(self):
		return self.budget_samples - self.sample_count


	@property
	def remaining_batches(self):
		return self.budget_batches - self.batch_count



class EpochBudgetMogul(BatchBudgetStatMogul, EpochStatMogul):
	@staticmethod
	def compute_epoch_budget(dataset_size, samples_per_batch, strict_batch_size=True,
	                   epochs=None, sample_limit=None, batch_limit=None, strict_limit=True):
		if epochs is None and sample_limit is None and batch_limit is None:
			return None, None, None  # infinite

		samples_per_epoch = dataset_size - int(strict_batch_size) * (dataset_size % samples_per_batch)
		batches_per_epoch = int(math.ceil(samples_per_epoch / samples_per_batch))

		total_samples = None if epochs is None else samples_per_epoch * epochs
		if batch_limit is not None:
			total = (batch_limit % batches_per_epoch) * samples_per_batch \
			        + (batch_limit // batches_per_epoch) * samples_per_epoch
			if total_samples is None or total < total_samples:
				total_samples = total
		if sample_limit is not None:
			total = samples_per_epoch * (sample_limit // samples_per_epoch)
			remainder = sample_limit % samples_per_epoch
			total += samples_per_batch * (remainder // samples_per_batch)
			remainder = remainder % samples_per_batch
			if remainder > 0:
				if strict_limit and not strict_batch_size:
					total += remainder
				elif not strict_limit:
					total += samples_per_batch
			if total_samples is None or total < total_samples:
				total_samples = total

		full_epochs = total_samples // samples_per_epoch
		remainder = total_samples % samples_per_epoch
		total_batches = full_epochs * batches_per_epoch + remainder // samples_per_batch
		remainder = remainder % samples_per_batch
		if not strict_batch_size and remainder > 0:
			total_batches += 1

		return total_samples, total_batches, full_epochs


	@property
	def full_epochs(self) -> Optional[int]:
		raise NotImplementedError


	@property
	def remaining_epochs(self):
		return self.full_epochs - self.completed_epochs



# class BudgetMogul(BatchBudgetMogul, OptimBudgetMogul):
# 	pass



########################################################################################################################



class SimpleTrainer(DynamicMogul):
	def __init__(self, model, *, optim=None, **kwargs):
		if optim is None:
			optim = model.default_optim()
		super().__init__(**kwargs)
		self.model = model
		self.optim = optim


	def fit(self, dataset):
		for ctx in self.iterate(dataset):
			out = self.step(ctx)
		raise NotImplementedError
		# return out


	@staticmethod
	def iterate(dataset):
		yield from dataset


	def step(self, ctx):
		self.optim.step(ctx)



class Checkpoint(SimpleTrainer):
	def checkpoint(self, ctx):
		pass



class Evaluatable(SimpleTrainer):
	def evaluate(self, dataset): # valset or testset
		pass



