
import sys, os
from pathlib import Path
import yaml

import numpy as np
# import torch
# from torch import nn
# from torch.nn import functional as F
# import torchvision

from omnibelt import unspecified_argument, agnostic
import omnifig as fig

from collections import OrderedDict
from functools import lru_cache

import omniplex as od
from omniplex import toy
from omniplex import Builder, HierarchyBuilder, RegisteredProduct, MatchingBuilder, RegistryBuilder, \
	register_builder, get_builder
from omniplex import BudgetLoader
from omniplex import hparam, inherit_hparams, submodule, submachine, spaces
from omniplex import Guru, Context, material, space, indicator, machine, Structured, Dataset, Datastream, Buffer

from omniplex import Spec, Builder, InitWall
from omniplex import toy

from omniplex.persistent import Rooted



# class ImageBuffer(Buffer):
# 	def process_image(self, image):
# 		if not self.space.as_bytes:
# 			return image.float().div(255)
# 		return image
#
#
# 	def get_from(self, source, gizmo=None):
# 		return self.process_image(super().get_from(source, gizmo=gizmo))



class RootedDataset(Dataset):
	_dirname = None

	@hparam(inherit=True)
	def root(self):
		path = Path(os.getenv('OMNIDATA_PATH', 'local_data/')) / 'datasets'
		if self._dirname is not None:
			return path / self._dirname
		return path



class _Torchvision_Toy_Dataset(RootedDataset):
	resize = hparam(True)
	mode = hparam(None)
	download = hparam(False)
	_as_bytes = hparam(False)


	def _expected_size(self):
		return 10000 if self.mode == 'test' else 60000


	@material.from_indices('image')
	def get_observation(self, indices):
		images = self.images[indices]
		if self._as_bytes:
			return images
		return images.float().div(255)
	@space('image')
	def observation_space(self):
		size = (32, 32) if self.resize else (28, 28)
		return spaces.Pixels(1, *size, as_bytes=self._as_bytes)


	@material.from_indices('target')
	def get_target(self, indices):
		return self.targets[indices]
	@space('target')
	def target_space(self):
		return spaces.Categorical(10 if self._target_names is None else self._target_names)


	def _get_source_kwargs(self, root=unspecified_argument, train=unspecified_argument,
	                       download=unspecified_argument, **kwargs):
		if root is unspecified_argument:
			kwargs['root'] = self.root
		if train is unspecified_argument:
			kwargs['train'] = self.mode != 'test'
		if download is unspecified_argument:
			kwargs['download'] = self.download
		return kwargs


	_source_type = None
	_target_attr = 'targets'
	_target_names = None


	# @agnostic
	# def is_downloaded(self):
	# 	return True

	# def download(self):
	# 	self._create_source(download=True)


	def _create_source(self, **kwargs):
		src_kwargs = self._get_source_kwargs(**kwargs)
		src = self._source_type(**src_kwargs)
		return src


	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)

		src = self._create_source()

		images = src.data
		if isinstance(images, np.ndarray):
			images = torch.as_tensor(images)
		if images.ndimension() == 3:
			images = images.unsqueeze(1)
		if images.size(1) not in {1,3}:
			images = images.permute(0,3,1,2)
		if self.resize:
			images = F.interpolate(images.float(), (32, 32), mode='bilinear').round().byte()
		self.images = images

		targets = getattr(src, self._target_attr)
		if not isinstance(targets, torch.Tensor):
			targets = torch.as_tensor(targets)
		self.targets = targets



@inherit_hparams('resize', 'mode', 'download')
class MNIST(_Torchvision_Toy_Dataset):
	_dirname = 'mnist'
	# _source_type = torchvision.datasets.MNIST



@inherit_hparams('resize', 'mode', 'download')
class KMNIST(_Torchvision_Toy_Dataset):
	_dirname = 'kmnist'
	# _source_type = torchvision.datasets.KMNIST
	_target_names = ['お', 'き', 'す', 'つ', 'な', 'は', 'ま', 'や', 'れ', 'を']



def test_mnist():

	print()
	print('\n'.join(map(str, MNIST.signatures())))

	dataset = MNIST(download=True)

	# dataset.prepare() # this will actually load the dataset (after downloading from the internet)

	print()
	print(dataset)

	print()
	print('\n'.join(map(str, dataset.signatures())))


