import numpy as np
import torch

from ..materials import Materialed, material
from ...structure import spaces, Decoder, Generator, NormalDistribution
from ...features import Seeded
from ...parameters import hparam, inherit_hparams

from ..flavors import Synthetic, Sampledstream
from ..top import Datastream, Dataset, Buffer



class ManifoldStream(Synthetic, Datastream, Seeded, Decoder, Generator):
	class Batch(Synthetic, Datastream.Batch):
		pass

	observation = material() # get

	@observation.transformation # get_key
	def decode(self, mechanism):
		raise NotImplementedError

	manifold = material('target', 'mechanism')

	@manifold.get_from_size
	def generate_mechanism(self, N):
		with self.force_rng(rng=self.rng):
			return self.mechanism_space.sample(N)

	def generate(self, N): # generates observations
		return self.decode(self.generate_mechanism(N))



class Stochastic(ManifoldStream):
	observation = material(src='observation')

	@observation.transformation # get_key
	def generate_observation_from_mechanism(self, mechanism):
		with self.force_rng(rng=self.rng):
			return self.decode_distrib(mechanism).sample()

	def decode_distrib(self, mechanism):
		return self._decode_distrib_from_mean(self.decode(mechanism))

	def _decode_distrib_from_mean(self, mean):
		raise NotImplementedError



class Noisy(Stochastic):
	noise_std = hparam(0., space=spaces.HalfBound(min=0.))#, alias='noise-std')

	def _decode_distrib_from_mean(self, mean):
		return NormalDistribution(mean, self.noise_std * torch.ones_like(mean))



class SwissRoll(ManifoldStream):
	Ax = hparam(np.pi / 2, space=spaces.HalfBound(min=0.))
	Ay = hparam(21., space=spaces.HalfBound(min=0.))
	Az = hparam(np.pi / 2, space=spaces.HalfBound(min=0.))

	freq = hparam(0.5, space=spaces.HalfBound(min=0.))
	tmin = hparam(3., space=spaces.HalfBound(min=0.))
	tmax = hparam(9., space=spaces.HalfBound(min=0.))

	manifold = material(replaces='mechanism')

	@manifold.space
	def mechanism_space(self):
		return spaces.Joint(
			spaces.Bound(min=self.tmin, max=self.tmax),
			spaces.Bound(min=0., max=1.),
		)

	target = material(replaces='target')

	@target.space
	def target_space(self):
		return self.mechanism_space[0]

	@target.transformation
	def get_target_from_mechanism(self, mechanism):
		return mechanism.narrow(-1,0,1)

	observation = material(replaces='observation')

	@observation.space
	def observation_space(self):
		return spaces.Joint(
			spaces.Bound(min=-self.Ax * self.tmax, max=self.Ax * self.tmax),
			spaces.Bound(min=0., max=self.Ay),
			spaces.Bound(min=-self.Az * self.tmax, max=self.Az * self.tmax),
		)

	def get_observation_from_mechanism(self, mechanism):
		theta = mechanism.narrow(-1,0,1)
		height = mechanism.narrow(-1,1,1)

		pts = torch.cat([
			self.Ax * theta * theta.mul(self.freq*np.pi).cos(),
			self.Ay * height,
			self.Az * theta * theta.mul(self.freq*np.pi).sin(),
		], -1)
		return pts



class RandomMapping(Dataset):
	N = hparam(1000, space=spaces.HalfBound(min=1))
	D = hparam(10, space=spaces.HalfBound(min=1))
	M = hparam(2, space=spaces.HalfBound(min=1))

	@material(space=spaces.Unbound())
	def X(self):
		return torch.randn(self.N, self.D)
	@X.space
	def X_space(self):
		return spaces.Unbound(self.D)

	class Y_Buffer(Buffer):
		pass

	@material
	def Y(self):
		return self.Y_Buffer()
	@Y.space
	def Y_space(self):
		return spaces.Unbound(self.M)



class MNIST(Dataset):
	class ImageBuffer(Buffer):
		pass

	@material
	def observation(self):
		size = (32, 32) if self.resize else (28, 28)
		return self.ImageBuffer(space=spaces.Pixels(1, *size, as_bytes=self._as_bytes))
	@observation.get_from_indices
	def get_observation(self, indices):
		return self.observation.data[indices]



class RandomCrop(MNIST):
	observation = material(replaces='observation')

	@observation.get_from_indices
	def get_observation(self, indices):
		return super().get_observation(indices).random_crop(self.size)


class RandomCrop2(MNIST):
	original = material('original', replaces='observation')

	observation = material(replaces='observation')

	@observation.transformation
	def get_cropped_observation(self, original):
		return original.random_crop(self.size)










