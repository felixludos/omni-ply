import os
import json
# import h5py as hf
# import torch
from pathlib import Path
from omnibelt import unspecified_argument, agnostic, agnosticproperty, md5

from ..structure import spaces
from ..parameters import hparam, submodule
from ..persistent import Rooted
from ..features import Named, Seedable

from .abstract import AbstractDataRouter
from .routers import Observation, Supervised, Labeled, Synthetic, DataCollection
from .top import Dataset, Datastream, Buffer



class Sampledstream(Dataset, Seedable): # Datastream -> Dataset
	stream = submodule(builder='stream')
	n_samples = hparam(required=True, space=spaces.Naturals(), inherit=True)
	sampler_seed = hparam(16283393149723337453, hidden=True)


	def __init__(self, n_samples: int, **kwargs):
		super().__init__(**kwargs)
		self.n_samples = n_samples
		for gizmo in self.stream.gizmos():
			self.register_buffer(gizmo, space=self.stream.space_of(gizmo))


	def _expected_size(self):
		return self.n_samples


	def _title(self):
		return f'{self.stream.title}[{self.n_samples}]'


	def _sample_stream_content(self, n_samples=None):
		# replacing stream with fixed samples
		if n_samples is None:
			n_samples = self.n_samples
		batch = self.stream.batch(n_samples, seed=self.sampler_seed) # optionally sample in smaller batches
		# batch.reset_rng(self.sampler_seed)
		for gizmo in batch.gizmos():
			buffer = self.get_buffer(gizmo)
			data = batch[gizmo]
			buffer.data = data


	def _prepare(self, **kwargs):
		out = super()._prepare( **kwargs)
		self._sample_stream_content()
		return out


	def space_of(self, gizmo: str):
		try:
			return super().space_of(gizmo)
		except self._ToolFailedError:
			return self.stream.space_of(gizmo)



class SimpleSampledStream(Sampledstream):
	_source_cls = None
	_source_hyperparameters = None
	def __init_subclass__(cls, source_cls=None, **kwargs):
		super().__init_subclass__(**kwargs)
		if source_cls is not None:
			cls._source_cls = source_cls
			hparams = []
			for name, value in source_cls.named_hyperparameters():
				setattr(cls, name, value.copy())
				hparams.append(name)
			cls._source_hyperparameters = tuple(hparams)


	@submodule(hidden=True)
	def stream(self):
		return self._source_cls(**{name: getattr(self, name) for name in self._source_hyperparameters})


	@agnostic
	def signatures(self, owner = None):
		if isinstance(self, type):
			yield from self._source_cls.signatures(owner)
		else:
			yield from super().signatures(owner)



class ObservationDataset(Observation, Dataset):
	pass
	# class Batch(Observation, Dataset.Batch):
	# 	pass
	# class View(Observation, Dataset.View):
	# 	pass



class SupervisedDataset(Supervised, ObservationDataset):
	pass
	# class Batch(Supervised, ObservationDataset.Batch):
	# 	pass
	# class View(Supervised, ObservationDataset.View):
	# 	pass



class LabeledDataset(Labeled, SupervisedDataset):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.register_material_alias('target', 'label')


	# class Batch(Labeled, SupervisedDataset.Batch):
	# 	pass
	# class View(Labeled, SupervisedDataset.View):
	# 	pass


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


	# class Batch(Synthetic, LabeledDataset.Batch):
	# 	@property
	# 	def _distinct_mechanisms(self):
	# 		return self.source._distince_mechanisms
	# class View(Synthetic, LabeledDataset.View):
	# 	@property
	# 	def _distinct_mechanisms(self):
	# 		return self.source._distince_mechanisms


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



class RootedRouter(DataCollection, Rooted):
	_dirname = None

	@agnostic
	def _infer_root(self, root=None):
		if root is not None:
			return Path(root)
		return super()._infer_root(root=root) / 'datasets'


	@agnosticproperty
	def root(self):
		dname = self._dirname
		assert dname is not None, 'missing dataset directory name'
		return self._infer_root() / dname


	@agnostic
	def get_aux_path(self):
		root = self.root / 'aux'
		root.mkdir(parents=True, exist_ok=True)
		return root


	# def _find_path(self, dataset_name='', file_name=None, root=None):
	# 	if root is None:
	# 		root = self.root
	# 	*other, dataset_name = dataset_name.split('.')
	# 	if file_name is None:
	# 		file_name = '.'.join(other) if len(other) else self.name
	# 	path = root / f'{file_name}.h5'
	# 	return path, dataset_name
	#
	#
	# _default_hdf_buffer_type = HDFBuffer
	# def register_hdf_buffer(self, name, dataset_name, file_name=None, root=None,
	#                         buffer_type=None, path=None, **kwargs):
	# 	if buffer_type is None:
	# 		buffer_type = self._default_hdf_buffer_type
	# 	if path is None:
	# 		path, dataset_name = self._find_path(dataset_name, file_name=file_name, root=root)
	# 	return self.register_buffer(name, buffer_type=buffer_type, dataset_name=dataset_name, path=path, **kwargs)
	#
	#
	# @staticmethod
	# def create_hdf_dataset(path, dataset_name, data=None, meta=None, dtype=None, shape=None):
	# 	# if file_name is unspecified_argument:
	# 	# 	file_name = 'aux'
	# 	# if path is None:
	# 	# 	path, dataset_name = self._find_path(dataset_name, file_name=file_name, root=root)
	#
	# 	if isinstance(data, torch.Tensor):
	# 		data = data.detach().cpu().numpy()
	# 	with hf.File(path, 'a') as f:
	# 		if data is not None or (dtype is not None and shape is not None):
	# 			f.create_dataset(dataset_name, data=data, dtype=dtype, shape=shape)
	# 		if meta is not None:
	# 			f.attrs[dataset_name] = json.dumps(meta, sort_keys=True)
	# 	return path, dataset_name



class DownloadableRouter(RootedRouter):
	def __init__(self, download=False, **kwargs):
		super().__init__(**kwargs)
		self._auto_download = download

	def _prepare(self, source=None, **kwargs):
		if not self.is_downloaded():
			if self._auto_download:
				self.download()
			else:
				raise self.DatasetNotDownloaded(self.title)
		super()._prepare(source=source, **kwargs)

	@agnostic
	def is_downloaded(self):
		raise NotImplementedError

	@classmethod
	def download(cls, **kwargs):
		raise NotImplementedError


	class DatasetNotDownloaded(FileNotFoundError):
		def __init__(self, name):
			super().__init__(f'use download=True to enable automatic download for {name}.')



class ImageBuffer(Buffer):
	def process_image(self, image):
		if not self.space.as_bytes:
			return image.float().div(255)
		return image


	def _get_from(self, source, key=None):
		return self.process_image(super()._get_from(source, key=key))





