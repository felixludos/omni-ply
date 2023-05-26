
from omnibelt import agnosticmethod
# import torch

from omniplex.parameters import abstract
from omniplex.modules.models import Function



class Extractor(Function, abstract.Extractor):
	@agnosticmethod
	def extract(self, observation):
		return self(observation)



class Encoder(Extractor, abstract.Encoder):
	@agnosticmethod
	def encode(self, observation):
		return self(observation)



class Decoder(Function, abstract.Decoder):
	@agnosticmethod
	def decode(self, latent):
		return self(latent)



class Generator(Function, abstract.Generator): # TODO update
	@agnosticmethod
	def sample(self, *shape, gen=None):
		raise NotImplementedError



class Discriminator(Function, abstract.Discriminator):
	@agnosticmethod
	def judge(self, observation):
		return self(observation)



class Augmentation(Function, abstract.Augmentation):
	@agnosticmethod
	def augment(self, observation):
		return self(observation)



class Criterion(Function, abstract.Criterion):
	@agnosticmethod
	def compare(self, observation1, observation2):
		return self(observation1, observation2)



class Metric(Criterion, abstract.Metric): # obeys triangle inequality
	@agnosticmethod
	def distance(self, observation1, observation2):
		return self(observation1, observation2)



class PathCriterion(Criterion, abstract.PathCriterion):
	@agnosticmethod
	def compare_path(self, path1, path2):
		return self(path1, path2)



class Interpolator(Function, abstract.Interpolator):
	# returns N steps to get from start to finish ("evenly spaces", by default)
	@staticmethod
	def interpolate(start, end, N):
		start, end = start.unsqueeze(1), end.unsqueeze(1)
		progress = torch.linspace(0., 1., steps=N+2, device=start.device).view(1, N+2, *[1] * len(start.shape[2:]))
		return start + (end - start) * progress



class Estimator(Function, abstract.Estimator):
	def predict(self, observation):
		return self(observation)



class Invertible(Function, abstract.Invertible):
	def forward(self, observation):
		return self(observation)


	@agnosticmethod
	def inverse(self, observation):
		raise NotImplementedError



class Compressor(Function, abstract.Compressor):
	def compress(self, observation):
		return self(observation)


	@staticmethod
	def decompress(data):
		raise NotImplementedError



class Quantizer(Function, abstract.Quantizer):
	def quantize(self, observation): # generally "removes" noise
		return self(observation)


	@staticmethod
	def dequantize(observation): # generally adds noise
		raise NotImplementedError


