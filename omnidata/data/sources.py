from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

from collections import OrderedDict
from omnibelt import unspecified_argument, get_printer

import math
# import torch

from ..structure import Generator, Sampler
from .. import util
from ..features import Seedable
from ..structure import spaces
# from ..parameters import Buildable
from .abstract import AbstractDataRouter, AbstractDataSource, \
	AbstractSelector, AbstractBatchable, AbstractCountableData, AbstractCountableSource
from .views import SizeSelector, IndexSelector

prt = get_printer(__file__)


# class BuildableData(Buildable, AbstractDataSource):
# 	pass



class Shufflable(Seedable):
	@staticmethod
	def _is_big_number(N):
		return N > 20000000


	def _shuffle_indices(self, N):
		# TODO: include a warning if cls._is_big_number(N)
		return torch.randint(N, size=(N,), generator=self.rng) \
			if self._is_big_number(N) else torch.randperm(N, generator=self.rng)



# class BatchableSource(AbstractBatchable):
# 	_Batch = None



class SpacedSource(AbstractDataSource):
	def __init__(self, *, space=None, **kwargs):
		super().__init__(**kwargs)
		self._space = space


	@property
	def space(self):
		return self._space
	@space.setter
	def space(self, space):
		self._space = space



# class SingleSource(AbstractDataSource):
# 	def _get_from(self, source, key=None):
# 		return self._get(source)
#
# 	@staticmethod
# 	def _get(source):
# 		raise NotImplementedError



# class SampleSource(AbstractDataSource, Sampler):
# 	_sample_key = None
# 	def _sample(self, shape, *, sample_key=None):
# 		if sample_key is unspecified_argument:
# 			sample_key = self._sample_key
# 		N = shape.numel()
# 		samples = self.sample_buffer(sample_key, N)
# 		return util.split_dim(samples, *shape)
#
#
# 	def sample_buffer(self, N, key):
# 		return self.get_from(N, key)



# class SelectorSource(AbstractDataSource, AbstractSelector):
# 	def get(self, key):
# 		return self.get_from(self, key)



# class GenerativeSource(AbstractDataSource, Generator):
# 	def _get_from(self, source, key):
# 		return self.generate(source.size)



class Subsetable(AbstractCountableSource, Shufflable):
	@staticmethod
	def _split_indices(indices, cut):
		assert cut != 0
		last = cut < 0
		cut = abs(cut)
		total = len(indices)
		if isinstance(cut, float):
			assert 0 < cut < 1
			cut = int(cut * total)
		part1, part2 = indices[:cut], indices[cut:]
		if last:
			part1, part2 = part2, part1
		return part1, part2
	
	_Subset = None # indexed view
	def subset(self, cut=None, *, indices=None, shuffle=False):
		# if not hard_copy:
		# 	raise NotImplementedError # TODO: hard copy
		if indices is None:
			assert cut is not None, 'Either cut or indices must be specified'
			indices, _ = self._split_indices(indices=self._shuffle_indices(self.size) \
				if shuffle else torch.arange(self.size), cut=cut)
		indices = self._validate_selection(indices)
		return self._Subset(source=self, indices=indices)
	


class Splitable(Subsetable):
	def split(self, splits, shuffle=False):
		auto_name = isinstance(splits, (list, tuple, set))
		if auto_name:
			named_cuts = [(f'part{i}', r) for i, r in enumerate(splits)]
		else:
			assert isinstance(splits, dict), f'unknown splits: {splits}'
			assert not any(x for x in splits if x is None), 'names of splits cannot be None'
			named_cuts = list(splits.items())
		names, cuts = zip(*sorted(named_cuts, key=lambda nr: (isinstance(nr[1], int), isinstance(nr[1], float),
		                                                      nr[1] is None, nr[0]), reverse=True))

		remaining = self.size
		nums = []
		itr = iter(cuts)
		for cut in itr:
			if isinstance(cut, int):
				nums.append(cut)
				remaining -= cut
			else:
				if isinstance(cut, float):
					ratios = []
					while isinstance(cut, float):
						ratios.append(cut)
						cut = next(itr, 'done')
					if len(cuts):
						rationums = [int(remaining * abs(ratio)) for ratio in ratios]
						nums.extend([int(math.copysign(1, r) * n) for r, n in zip(ratios, rationums)])
						remaining -= sum(rationums)
				if cut is None:
					pieces = len([cut, *itr])
					assert remaining > pieces, f'cant evenly distribute {remaining} samples into {pieces} cuts'
					evennums = [int(remaining // pieces) for _ in range(pieces)]
					nums.extend(evennums)
					remaining -= sum(evennums)

		if remaining > 0:
			nums[-1] += remaining

		indices = self._shuffle_indices(self.size) if shuffle else torch.arange(self.size)

		plan = dict(zip(names, nums))
		parts = {}
		for name in sorted(names):
			num = plan[name]
			part, indices = self._split_indices(indices, num)
			parts[name] = self.subset(indices=part)
		if auto_name:
			return [parts[name] for name, _ in named_cuts]
		return parts



class TensorSource(AbstractCountableData, AbstractDataSource): # TODO: make batchable
	def __init__(self, data=None, space=None, **kwargs):
		super().__init__(**kwargs)
		self._data = data
		self._space = space


	@property
	def is_ready(self):
		return self._data is not None


	@property
	def space(self):
		return self._space
	@space.setter
	def space(self, space):
		self._space = space


	def space_of(self, gizmo: str) -> spaces.Dim:
		return self.space


	@property
	def size(self):
		return len(self._data)


	@property
	def data(self):
		return self._data
	@data.setter
	def data(self, data):
		self._data = data


	def gizmos(self) -> Iterator[str]:
		yield from ()


	def get_from(self, source, gizmo=None):
		if source is None or not isinstance(source, IndexSelector):
			return self._data[:source.size] if isinstance(source, SizeSelector) else self._data
		return self.data[source.indices]



class MultiModed(Splitable): # TODO: splitting datasets into modes
	pass








# class ProcessDataset(Dataset):
#
# 	process = None # TODO: maybe machine?
#
# 	def _prepare(self, *args, **kwargs):
# 		raise NotImplementedError
#
#
#
# class RootedDataset(DataCollection, Rooted):
# 	@classmethod
# 	def _infer_root(cls, root=None):
# 		return super()._infer_root(root=root) / 'datasets'
#
#
# 	@agnostic
# 	def get_root(self, dataset_dir=None):
# 		if dataset_dir is None:
# 			dataset_dir = self.name
# 		root = super().get_root() / dataset_dir
# 		os.makedirs(str(root), exist_ok=True)
# 		return root
#
#
# 	def get_aux_root(self, dataset_dir=None):
# 		root = self.get_root(dataset_dir=dataset_dir) / 'aux'
# 		os.makedirs(str(root), exist_ok=True)
# 		return root
#
#
# 	def _find_path(self, dataset_name='', file_name=None, root=None):
# 		if root is None:
# 			root = self.root
# 		*other, dataset_name = dataset_name.split('.')
# 		if file_name is None:
# 			file_name = '.'.join(other) if len(other) else self.name
# 		path = root / f'{file_name}.h5'
# 		return path, dataset_name
#
#
# 	_default_hdf_buffer_type = HDFBuffer
# 	def register_hdf_buffer(self, name, dataset_name, file_name=None, root=None,
# 	                        buffer_type=None, path=None, **kwargs):
# 		if buffer_type is None:
# 			buffer_type = self._default_hdf_buffer_type
# 		if path is None:
# 			path, dataset_name = self._find_path(dataset_name, file_name=file_name, root=root)
# 		return self.register_buffer(name, buffer_type=buffer_type, dataset_name=dataset_name, path=path, **kwargs)
#
#
# 	@staticmethod
# 	def create_hdf_dataset(path, dataset_name, data=None, meta=None, dtype=None, shape=None):
# 		# if file_name is unspecified_argument:
# 		# 	file_name = 'aux'
# 		# if path is None:
# 		# 	path, dataset_name = self._find_path(dataset_name, file_name=file_name, root=root)
#
# 		if isinstance(data, torch.Tensor):
# 			data = data.detach().cpu().numpy()
# 		with hf.File(path, 'a') as f:
# 			if data is not None or (dtype is not None and shape is not None):
# 				f.create_dataset(dataset_name, data=data, dtype=dtype, shape=shape)
# 			if meta is not None:
# 				f.attrs[dataset_name] = json.dumps(meta, sort_keys=True)
# 		return path, dataset_name
#
#
#
# class DownloadableDataset(RootedDataset):
# 	def __init__(self, download=False, **kwargs):
# 		super().__init__(**kwargs)
# 		self._auto_download = download
#
#
# 	@classmethod
# 	def download(cls, **kwargs):
# 		raise NotImplementedError
#
#
# 	class DatasetNotDownloaded(FileNotFoundError):
# 		def __init__(self):
# 			super().__init__('use download=True to enable automatic download.')
#
#
#
# class EncodableDataset(ObservationDataset, RootedDataset):
# 	def __init__(self, encoder=None, replace_observation_key=None, encoded_key='encoded',
# 	             encoded_file_name='aux', encode_on_load=False, save_encoded=False, encode_pbar=None, **kwargs):
# 		super().__init__(**kwargs)
# 		self._replace_observation_key = replace_observation_key
# 		self._encoded_observation_key = encoded_key
# 		self._encoded_file_name = encoded_file_name
# 		self._encode_on_load = encode_on_load
# 		self._save_encoded = save_encoded
# 		self._encode_pbar = encode_pbar
# 		self.encoder = encoder
#
# 	@property
# 	def encoder(self): # TODO: make this a machine
# 		return self._encoder
# 	@encoder.setter
# 	def encoder(self, encoder):
# 		buffer = self.get_buffer(self._encoded_observation_key)
# 		if buffer is not None:
# 			buffer.encoder = encoder
# 		self._encoder = encoder
#
#
# 	def _get_code_path(self, file_name='aux', root=None):
# 		return None if file_name is None else self._find_path(file_name=file_name, root=root)[0]
#
#
# 	@staticmethod
# 	def _encoder_save_key(encoder):
# 		info = encoder.get_encoder_fingerprint()
# 		ident = md5(json.dumps(info, sort_keys=True))
# 		return ident, info
#
#
# 	def load_encoded_data(self, encoder=None, source_key='observation',
# 	                      batch_size=None, save_encoded=None,
# 	                      file_name=unspecified_argument, root=None):
# 		if encoder is None:
# 			encoder = self.encoder
# 		if file_name is unspecified_argument:
# 			file_name = self._encoded_file_name
# 		if save_encoded is None:
# 			save_encoded = self._save_encoded
# 		data = None
#
# 		path = self._get_code_path(file_name=file_name, root=root)
# 		if path is not None and path.exists() and encoder is not None:
# 			ident, _ = self._encoder_save_key(encoder)
# 			with hf.File(str(path), 'r') as f:
# 				if ident in f:
# 					data = f[ident][()]
# 					data = torch.from_numpy(data)
#
# 		if data is None and self._encode_on_load:
# 			batches = []
# 			for batch in self.get_iterator(batch_size=batch_size, shuffle=False, force_batch_size=False,
# 			                               pbar=self._encode_pbar):
# 				with torch.no_grad():
# 					batches.append(encoder(batch[source_key]))
#
# 			data = torch.cat(batches)
# 			if save_encoded:
# 				self.save_encoded_data(encoder, data, path)
#
# 		return data
#
#
# 	@classmethod
# 	def save_encoded_data(cls, encoder, data, path):
# 		ident, info = cls._encoder_save_key(encoder)
# 		cls.create_hdf_dataset(path, ident, data=data, meta=info)
#
#
# 	def _prepare(self, *args, **kwargs):
# 		super()._prepare(*args, **kwargs)
#
# 		if self._replace_observation_key is not None:
# 			self._encoded_observation_key = 'observation'
# 			self.register_buffer(self._replace_observation_key, self.get_buffer('observation'))
#
# 		self.register_buffer(self._encoded_observation_key,
# 		                     buffer=self.EncodedBuffer(encoder=self.encoder, source=self.get_buffer('observation'),
# 		                                               data=self.load_encoded_data()))
#
#
# 	class EncodedBuffer(BufferView):
# 		def __init__(self, encoder=None, max_batch_size=64, pbar=None, pbar_desc='encoding', **kwargs):
# 			super().__init__(**kwargs)
# 			# if encoder is not None and encoder_device is None:
# 			# 	encoder_device = getattr(encoder, 'device', None)
# 			# self._encoder_device = encoder_device
# 			self.encoder = encoder
# 			self.pbar = pbar
# 			self.pbar_desc = pbar_desc
# 			self.max_batch_size = max_batch_size
#
#
# 		@property
# 		def encoder(self):
# 			return self._encoder
# 		@encoder.setter
# 		def encoder(self, encoder):
# 			self._encoder = encoder
# 			if encoder is not None and hasattr(encoder, 'dout'):
# 				self.space = getattr(encoder, 'dout', None)
# 		# self._encoder_device = getattr(encoder, 'device', self._encoder_device)
#
#
# 		def _encode_raw_observations(self, observations):
# 			# device = observations.device
# 			if len(observations) > self.max_batch_size:
# 				samples = []
# 				batches = observations.split(self.max_batch_size)
# 				if self.pbar is not None:
# 					batches = self.pbar(batches, desc=self.pbar_desc)
# 				for batch in batches:
# 					# with torch.no_grad():
# 					# if self._encoder_device is not None:
# 					# 	batch = batch.to(self._encoder_device)
# 					samples.append(self.encoder.encode(batch)  )  # .to(device))
# 				return torch.cat(samples)
# 			# with torch.no_grad():
# 			# if self._encoder_device is not None:
# 			# 	observations = observations.to(self._encoder_device)
# 			return self.encoder.encode(observations  )  # .to(device)
#
#
# 		def _get(self, sel=None, **kwargs):
# 			sample = super()._get(sel=sel, **kwargs)
# 			if self.data is None and self.encoder is not None:
# 				sample = self._encode_raw_observations(sample)
# 			if sel is None:
# 				self.data = sample
# 			return sample
#
#
#
# class ImageDataset(ObservationDataset):
# 	class ImageBuffer(Buffer):
# 		def process_image(self, image):
# 			if not self.space.as_bytes:
# 				return image.float().div(255)
# 			return image
#
#
# 		def _get(self, *args, **kwargs):
# 			return self.process_image(super()._get(*args, **kwargs))
















