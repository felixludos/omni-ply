
# from ..persistent import Fingerprinted
from ..parameters import hparam, with_hparams, Parameterized

from .abstract import AbstractBatchable
from .routers import DataCollection, AutoCollection, BranchedDataRouter, AliasedCollection, CountableDataRouter
from .views import IndexView, CachedView, BatchBase, IndexBatch, BatchableView
from .sources import Splitable, TensorSource, SpacedSource, BatchableSource, BuildableData
from .progression import SetProgression, StreamProgression
from .materials import Materialed


class Batchable(AbstractBatchable, Parameterized):
	Batch = None
	Progression = StreamProgression

	batch_size = hparam(inherit=True)

	sample_limit = hparam(inherit=True)
	batch_limit = hparam(inherit=True)
	strict_limit = hparam(False, inherit=True, hidden=True)

	strict_batch_size = hparam(False, inherit=True, hidden=True)
	shuffle_batches = hparam(False, inherit=True, hidden=True)

	use_pbar = hparam(False, inherit=True, hidden=True)
	pbar_samples = hparam(True, inherit=True, hidden=True)

	@with_hparams
	def iterate(self, batch_size, sample_limit=None, batch_limit=None,
	            strict_limit=False, strict_batch_size=False,
				shuffle=None, shuffle_batches=False,
	            use_pbar=False, pbar_samples=True, **kwargs):
		if shuffle is None:
			shuffle = shuffle_batches
		return super().iterate(batch_size=batch_size, sample_limit=sample_limit, batch_limit=batch_limit,
		                       strict_limit=strict_limit, strict_batch_size=strict_batch_size,
		                       shuffle=shuffle, use_pbar=use_pbar, pbar_samples=pbar_samples, **kwargs)


class Epoched(Batchable):
	Progression = SetProgression

	epoch_limit = hparam(inherit=True)

	@with_hparams
	def iterate(self, batch_size, epochs=None, epoch_limit=None, **kwargs):
		if epoch_limit is None:
			epoch_limit = epochs
		return super().iterate(batch_size=batch_size, epochs=epoch_limit, **kwargs)



class Buffer(TensorSource, SpacedSource, BatchableSource, BuildableData):
	pass


class _FeaturedDataRouter(AutoCollection, AliasedCollection, BatchableSource,
                          Materialed, DataCollection, BuildableData):
	_SimpleMaterial = Buffer



class Datastream(Batchable, _FeaturedDataRouter): # not countable (but batchable)
	class Material(_FeaturedDataRouter.Material):
		pass
	class Batch(Batchable, BatchableView, CachedView, BatchBase):
		pass
	class View(BatchableView):
		pass

Batchable.Batch = Datastream.Batch


class Batch(Epoched, BatchableView, CachedView, IndexBatch):
	pass
Epoched.Batch = Batch


class Dataset(Splitable, CountableDataRouter, Epoched, _FeaturedDataRouter):
	Batch = Batch
	class Material(_FeaturedDataRouter.Material):
		pass
	class View(BatchableView, IndexView):
		pass
	Subset = View



class SimpleDataset(Dataset): # TODO: test with ints as keys
	_is_ready = True

	def __init__(self, *unnamed_data, **named_data):
		super().__init__()
		self._register_init_data(unnamed_data, named_data)

	def _register_init_data(self, unnamed_data, named_data):
		for i, x in enumerate(unnamed_data):
			self.register_material(i, x)
		for k, v in named_data.items():
			self.register_material(k, v)

















