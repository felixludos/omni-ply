import os
import json
import h5py as hf
import torch
from omnibelt import unspecified_argument, agnostic, md5

from ..structure import Metric, Generator
from ..persistent import Rooted
from ..parameters import Parameterized, Builder, ClassBuilder, Buildable

# from .abstract import BufferTransform
from .base import Dataset, DataSource, DataCollection
from .buffers import Buffer, BufferView, HDFBuffer



class BuildableDataset(DataCollection, Buildable):
	pass



class SimpleDataset(Dataset):
	_is_ready = True

	def __init__(self, **data):
		super().__init__(data=data)



class GenerativeDataset(Dataset, Generator):
	pass


class _ObservationInfo(DataSource):
	@property
	def din(self):
		return self.observation_space


	@property
	def observation_space(self):
		return self.space_of('observation')


	def get_observation(self, sel=None, **kwargs):
		return self.get('observation', sel=sel, **kwargs)



class ObservationDataset(_ObservationInfo, Dataset):
	sample_key = 'observation'


	class Batch(_ObservationInfo, Dataset.Batch):
		pass
	class View(_ObservationInfo, Dataset.View):
		pass


	def sample_observation(self, *shape, gen=None):
		return self.sample(*shape, gen=gen, sample_key='observation')



class _SupervisionInfo(_ObservationInfo, Metric):
	@property
	def dout(self):
		return self.target_space


	@property
	def target_space(self):
		return self.space_of('target')


	def get_target(self, sel=None, **kwargs):
		return self.get('target', sel=sel, **kwargs)


	def difference(self, a, b, standardize=None):
		return self.dout.difference(a, b, standardize=standardize)


	def measure(self, a, b, standardize=None):
		return self.dout.measure(a, b, standardize=standardize)


	def distance(self, a, b, standardize=None):
		return self.dout.distance(a, b, standardize=standardize)



class SupervisedDataset(_SupervisionInfo, ObservationDataset):
	class Batch(_SupervisionInfo, ObservationDataset.Batch):
		pass
	class View(_SupervisionInfo, ObservationDataset.View):
		pass


	def sample_target(self, *shape, gen=None):
		return self.sample(*shape, gen=gen, sample_key='target')



class _LabeledInfo(_SupervisionInfo):
	@property
	def label_space(self):
		return self.space_of('label')


	def get_label(self, sel=None, **kwargs):
		return self.get('label', sel=sel, **kwargs)



class LabeledDataset(_LabeledInfo, SupervisedDataset):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.register_buffer('target', 'label')


	class Batch(_LabeledInfo, SupervisedDataset.Batch):
		pass
	class View(_LabeledInfo, SupervisedDataset.View):
		pass


	def sample_label(self, *shape, gen=None):
		return self.sample(*shape, gen=gen, sample_key='label')


	def generate_observation_from_label(self, label, gen=None):
		raise NotImplementedError



# Labeled means there exists a deterministic mapping from labels to observations
# (not including possible subsequent additive noise)



class _SyntheticInfo(_LabeledInfo):
	_distinct_mechanisms = True


	@property
	def mechanism_space(self):
		return self.space_of('mechanism')


	def transform_to_mechanisms(self, data):
		if not self._distinct_mechanisms:
			return data
		return self.mechanism_space.transform(data, self.label_space)


	def transform_to_labels(self, data):
		if not self._distinct_mechanisms:
			return data
		return self.label_space.transform(data, self.mechanism_space)



class SyntheticDataset(_SyntheticInfo, LabeledDataset):
	# _standardize_scale = True
	_use_mechanisms = True

	def __init__(self, use_mechanisms=None, **kwargs):
		# standardize_scale=None,
		super().__init__(**kwargs)
		# if standardize_scale is not None:
		# 	self._standardize_scale = standardize_scale
		if use_mechanisms is not None:
			self._use_mechanisms = use_mechanisms
		self.register_buffer('mechanism', 'label')
		self.register_buffer('target', 'mechanism' if self._use_mechanisms else 'label')


	class Batch(_SyntheticInfo, LabeledDataset.Batch):
		@property
		def _distinct_mechanisms(self):
			return self.source._distince_mechanisms
	class View(_SyntheticInfo, LabeledDataset.View):
		@property
		def _distinct_mechanisms(self):
			return self.source._distince_mechanisms


	def sample_mechanism(self, *shape, gen=None):
		return self.sample(*shape, gen=gen, sample_key='mechanism')


	def generate_mechanism(self, *shape):
		return self.mechanism_space.sample(*shape, gen=self.gen)


	def generate_observation_from_label(self, label, gen=None):
		return self.generate_observation_from_mechanism(self.transform_to_mechanisms(label), gen=gen)


	def generate_observation_from_mechanism(self, mechanism, gen=None):
		raise NotImplementedError
# Synthetic means the mapping is known (and available, usually only for evaluation)
# TODO: separate labels and mechanisms



class ProcessDataset(Dataset):

	process = None # TODO: maybe machine?

	def _prepare(self, *args, **kwargs):
		raise NotImplementedError



class RootedDataset(DataCollection, Rooted):
	@classmethod
	def _infer_root(cls, root=None):
		return super()._infer_root(root=root) / 'datasets'


	@agnostic
	def get_root(self, dataset_dir=None):
		if dataset_dir is None:
			dataset_dir = self.name
		root = super().get_root() / dataset_dir
		os.makedirs(str(root), exist_ok=True)
		return root


	def get_aux_root(self, dataset_dir=None):
		root = self.get_root(dataset_dir=dataset_dir) / 'aux'
		os.makedirs(str(root), exist_ok=True)
		return root


	def _find_path(self, dataset_name='', file_name=None, root=None):
		if root is None:
			root = self.root
		*other, dataset_name = dataset_name.split('.')
		if file_name is None:
			file_name = '.'.join(other) if len(other) else self.name
		path = root / f'{file_name}.h5'
		return path, dataset_name


	_default_hdf_buffer_type = HDFBuffer
	def register_hdf_buffer(self, name, dataset_name, file_name=None, root=None,
	                        buffer_type=None, path=None, **kwargs):
		if buffer_type is None:
			buffer_type = self._default_hdf_buffer_type
		if path is None:
			path, dataset_name = self._find_path(dataset_name, file_name=file_name, root=root)
		return self.register_buffer(name, buffer_type=buffer_type, dataset_name=dataset_name, path=path, **kwargs)


	@staticmethod
	def create_hdf_dataset(path, dataset_name, data=None, meta=None, dtype=None, shape=None):
		# if file_name is unspecified_argument:
		# 	file_name = 'aux'
		# if path is None:
		# 	path, dataset_name = self._find_path(dataset_name, file_name=file_name, root=root)

		if isinstance(data, torch.Tensor):
			data = data.detach().cpu().numpy()
		with hf.File(path, 'a') as f:
			if data is not None or (dtype is not None and shape is not None):
				f.create_dataset(dataset_name, data=data, dtype=dtype, shape=shape)
			if meta is not None:
				f.attrs[dataset_name] = json.dumps(meta, sort_keys=True)
		return path, dataset_name



class DownloadableDataset(RootedDataset):
	def __init__(self, download=False, **kwargs):
		super().__init__(**kwargs)
		self._auto_download = download


	@classmethod
	def download(cls, **kwargs):
		raise NotImplementedError


	class DatasetNotDownloaded(FileNotFoundError):
		def __init__(self):
			super().__init__('use download=True to enable automatic download.')



class EncodableDataset(ObservationDataset, RootedDataset):
	def __init__(self, encoder=None, replace_observation_key=None, encoded_key='encoded',
	             encoded_file_name='aux', encode_on_load=False, save_encoded=False, encode_pbar=None, **kwargs):
		super().__init__(**kwargs)
		self._replace_observation_key = replace_observation_key
		self._encoded_observation_key = encoded_key
		self._encoded_file_name = encoded_file_name
		self._encode_on_load = encode_on_load
		self._save_encoded = save_encoded
		self._encode_pbar = encode_pbar
		self.encoder = encoder

	@property
	def encoder(self): # TODO: make this a machine
		return self._encoder
	@encoder.setter
	def encoder(self, encoder):
		buffer = self.get_buffer(self._encoded_observation_key)
		if buffer is not None:
			buffer.encoder = encoder
		self._encoder = encoder


	def _get_code_path(self, file_name='aux', root=None):
		return None if file_name is None else self._find_path(file_name=file_name, root=root)[0]


	@staticmethod
	def _encoder_save_key(encoder):
		info = encoder.get_encoder_fingerprint()
		ident = md5(json.dumps(info, sort_keys=True))
		return ident, info


	def load_encoded_data(self, encoder=None, source_key='observation',
	                      batch_size=None, save_encoded=None,
	                      file_name=unspecified_argument, root=None):
		if encoder is None:
			encoder = self.encoder
		if file_name is unspecified_argument:
			file_name = self._encoded_file_name
		if save_encoded is None:
			save_encoded = self._save_encoded
		data = None

		path = self._get_code_path(file_name=file_name, root=root)
		if path is not None and path.exists() and encoder is not None:
			ident, _ = self._encoder_save_key(encoder)
			with hf.File(str(path), 'r') as f:
				if ident in f:
					data = f[ident][()]
					data = torch.from_numpy(data)

		if data is None and self._encode_on_load:
			batches = []
			for batch in self.get_iterator(batch_size=batch_size, shuffle=False, force_batch_size=False,
			                               pbar=self._encode_pbar):
				with torch.no_grad():
					batches.append(encoder(batch[source_key]))

			data = torch.cat(batches)
			if save_encoded:
				self.save_encoded_data(encoder, data, path)

		return data


	@classmethod
	def save_encoded_data(cls, encoder, data, path):
		ident, info = cls._encoder_save_key(encoder)
		cls.create_hdf_dataset(path, ident, data=data, meta=info)


	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)

		if self._replace_observation_key is not None:
			self._encoded_observation_key = 'observation'
			self.register_buffer(self._replace_observation_key, self.get_buffer('observation'))

		self.register_buffer(self._encoded_observation_key,
		                     buffer=self.EncodedBuffer(encoder=self.encoder, source=self.get_buffer('observation'),
		                                               data=self.load_encoded_data()))


	class EncodedBuffer(BufferView):
		def __init__(self, encoder=None, max_batch_size=64, pbar=None, pbar_desc='encoding', **kwargs):
			super().__init__(**kwargs)
			# if encoder is not None and encoder_device is None:
			# 	encoder_device = getattr(encoder, 'device', None)
			# self._encoder_device = encoder_device
			self.encoder = encoder
			self.pbar = pbar
			self.pbar_desc = pbar_desc
			self.max_batch_size = max_batch_size


		@property
		def encoder(self):
			return self._encoder
		@encoder.setter
		def encoder(self, encoder):
			self._encoder = encoder
			if encoder is not None and hasattr(encoder, 'dout'):
				self.space = getattr(encoder, 'dout', None)
		# self._encoder_device = getattr(encoder, 'device', self._encoder_device)


		def _encode_raw_observations(self, observations):
			# device = observations.device
			if len(observations) > self.max_batch_size:
				samples = []
				batches = observations.split(self.max_batch_size)
				if self.pbar is not None:
					batches = self.pbar(batches, desc=self.pbar_desc)
				for batch in batches:
					# with torch.no_grad():
					# if self._encoder_device is not None:
					# 	batch = batch.to(self._encoder_device)
					samples.append(self.encoder.encode(batch)  )  # .to(device))
				return torch.cat(samples)
			# with torch.no_grad():
			# if self._encoder_device is not None:
			# 	observations = observations.to(self._encoder_device)
			return self.encoder.encode(observations  )  # .to(device)


		def _get(self, sel=None, **kwargs):
			sample = super()._get(sel=sel, **kwargs)
			if self.data is None and self.encoder is not None:
				sample = self._encode_raw_observations(sample)
			if sel is None:
				self.data = sample
			return sample



class ImageDataset(ObservationDataset):
	class ImageBuffer(Buffer):
		def process_image(self, image):
			if not self.space.as_bytes:
				return image.float().div(255)
			return image


		def _get(self, *args, **kwargs):
			return self.process_image(super()._get(*args, **kwargs))






