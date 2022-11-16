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
from .routers import AbstractDataRouter
from .sources import SampleSource
from .common import Dataset


# class BuildableDataset(DataCollection, Buildable):
# 	pass



class SimpleDataset(Dataset):
	_is_ready = True

	def __init__(self, **data):
		super().__init__()
		self._register_init_data(data)

	def _register_init_data(self, data):
		for k, v in data.items():
			self.register_material(k, v)



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



class ObservationDataset(Observation, Dataset):
	class Batch(Observation, Dataset.Batch):
		pass
	class View(Observation, Dataset.View):
		pass



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



class SupervisedDataset(Supervised, ObservationDataset):
	class Batch(Supervised, ObservationDataset.Batch):
		pass
	class View(Supervised, ObservationDataset.View):
		pass



class Labeled(Supervised):
	@property
	def label_space(self):
		return self.space_of('label')
	@label_space.setter
	def label_space(self, space):
		self.get_material('label').space = space



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



class Synthetic(Labeled): # TODO: include auto alias
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





