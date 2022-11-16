

from .routers import DataCollection, SimpleCollection, BranchedDataRouter, AliasedCollection
from .views import IndexView, CachedView, BatchBase, IndexBatch, BatchableView
from .sources import Subsetable, Splitable, TensorSource, SpacedSource, BatchableSource
from .progression import TrackedProgression, BarredProgression


class Buffer(TensorSource, SpacedSource, BatchableSource):
	pass



class Datastream(SimpleCollection, AliasedCollection, BatchableSource, DataCollection): # not size (but batchable)
	Progression = BarredProgression
	class Batch(BatchableView, CachedView, BatchBase):
		pass
	class View(BatchableView):
		pass



class Dataset(Splitable, SimpleCollection, AliasedCollection, BatchableSource, DataCollection):
	_SimpleMaterial = Buffer
	Progression = TrackedProgression
	class Batch(BatchableView, CachedView, IndexBatch):
		pass
	class View(BatchableView, IndexView):
		pass
	Subset = View



class Sampledstream(Dataset, Datastream):
	_StreamTable = Dataset._MaterialsTable

	def __init__(self, n_samples, *args, stream_table=None, default_len=None, **kwargs):
		if default_len is None:
			default_len = n_samples
		if stream_table is None:
			stream_table = self._StreamTable()
		super().__init__(*args, default_len=default_len, **kwargs)
		self._n_samples = n_samples
		self._stream_materials = stream_table

	def _prepare(self, **kwargs):
		out = super()._prepare( **kwargs)

		# replacing stream with fixed samples

		n_samples = len(self)
		batch = self.batch(n_samples)
		for key, material in self.named_materials():
			self._stream_materials[key] = material
			self.register_material(key, batch[key], space=material.space)
		return out















