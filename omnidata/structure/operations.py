import torch

from omnibelt import agnostic
from ..features import Seeded


class Extractor:
	@agnostic
	def extract(self, observation):
		raise NotImplementedError



class Encoder(Extractor):
	@agnostic
	def extract(self, observation):
		return self.encode(observation)


	@agnostic
	def encode(self, observation):
		raise NotImplementedError



class Decoder:
	@agnostic
	def decode(self, latent):
		raise NotImplementedError



class Generator:
	@agnostic
	def sample(self, *shape, gen=None):
		raise NotImplementedError



class Discriminator:
	@agnostic
	def judge(self, observation):
		raise NotImplementedError



class Augmentation:
	@agnostic
	def augment(self, observation):
		raise NotImplementedError



class Criterion:
	@agnostic
	def compare(self, observation1, observation2):
		raise NotImplementedError



class Metric(Criterion): # obeys triangle inequality
	@agnostic
	def distance(self, observation1, observation2):
		raise NotImplementedError


	@agnostic
	def compare(self, observation1, observation2):
		return self.distance(observation1, observation2)



class PathCriterion(Criterion):
	@agnostic
	def compare(self, observation1, observation2):
		return self.compare_path(observation1, observation2)


	@agnostic
	def compare_path(self, path1, path2):
		raise NotImplementedError



class Interpolator: # returns N steps to get from start to finish ("evenly spaces", by default)
	@staticmethod
	def interpolate(start, end, N):
		raise NotImplementedError



class Estimator:
	@agnostic
	def predict(self, observation):
		raise NotImplementedError



class Invertible:
	@agnostic
	def forward(self, observation):
		raise NotImplementedError


	@agnostic
	def inverse(self, observation):
		raise NotImplementedError



class Compressor:
	@staticmethod
	def compress(observation):
		raise NotImplementedError


	@staticmethod
	def decompress(data):
		raise NotImplementedError



class Quantizer:
	@staticmethod
	def quantize(observation): # generally "removes" noise
		raise NotImplementedError


	@staticmethod
	def dequantize(observation): # generally adds noise
		raise NotImplementedError



class Sampler(Seeded, Generator):
	def sample(self, *shape, gen=None, **kwargs):
		if gen is None:
			gen = self.gen
		return self._sample(torch.Size(shape), gen=gen, **kwargs)


	def _sample(self, shape, gen, **kwargs):
		raise NotImplementedError
