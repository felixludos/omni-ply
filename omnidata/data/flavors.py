import os
import json
import h5py as hf
import torch
from omnibelt import unspecified_argument, agnostic, md5

from ..structure import Metric, Generator, Sampler
from ..persistent import Rooted
from ..parameters import Parameterized, Builder, ClassBuilder, Buildable

# from .abstract import BufferTransform
# from .base import Dataset, DataSource, DataCollection
# from .buffers import Buffer, BufferView, HDFBuffer
from .routers import Observation, Supervised, Labeled, Synthetic
from .top import Dataset, Datastream



class Sampledstream(Dataset, Datastream): # Datastream -> Dataset
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
		batch = self.Batch(source=self, size=n_samples) # mostly for caching
		for key, material in self.named_materials():
			self._stream_materials[key] = material
			self.register_material(key, batch[key], space=material.space)
		return out



class ObservationDataset(Observation, Dataset):
	class Batch(Observation, Dataset.Batch):
		pass
	class View(Observation, Dataset.View):
		pass



class SupervisedDataset(Supervised, ObservationDataset):
	class Batch(Supervised, ObservationDataset.Batch):
		pass
	class View(Supervised, ObservationDataset.View):
		pass



class LabeledDataset(Labeled, SupervisedDataset):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.register_material_alias('target', 'label')


	class Batch(Labeled, SupervisedDataset.Batch):
		pass
	class View(Labeled, SupervisedDataset.View):
		pass


	# def generate_observation_from_label(self, label, gen=None):
	# 	raise NotImplementedError



# Labeled means there exists a deterministic mapping from labels to observations
# (not including possible subsequent additive noise)



class SyntheticDataset(Synthetic, LabeledDataset):
	_use_mechanisms = True

	def __init__(self, use_mechanisms=None, **kwargs):
		super().__init__(**kwargs)
		if use_mechanisms is not None:
			self._use_mechanisms = use_mechanisms
		self.register_material_alias('mechanism', 'label')
		self.register_material_alias('target', 'mechanism' if self._use_mechanisms else 'label')


	class Batch(Synthetic, LabeledDataset.Batch):
		@property
		def _distinct_mechanisms(self):
			return self.source._distince_mechanisms
	class View(Synthetic, LabeledDataset.View):
		@property
		def _distinct_mechanisms(self):
			return self.source._distince_mechanisms


	# def generate_mechanism(self, *shape):
	# 	return self.mechanism_space.sample(*shape, gen=self.gen)
	#
	#
	# def generate_observation_from_label(self, label, gen=None):
	# 	return self.generate_observation_from_mechanism(self.transform_to_mechanisms(label), gen=gen)
	#
	#
	# def generate_observation_from_mechanism(self, mechanism, gen=None):
	# 	raise NotImplementedError
# Synthetic means the mapping is known (and available, usually only for evaluation)
# TODO: separate labels and mechanisms





