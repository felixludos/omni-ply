import numpy as np
import torch
# from sklearn.datasets import make_swiss_roll

# from ..materials import Materialed, material
from ...structure import spaces, Decoder, Generator, NormalDistribution
from ...features import Seeded
from ...parameters import hparam, inherit_hparams
from ...tools import material, machine, space

from ..flavors import Synthetic, Sampledstream
from ..top import Datastream



class ManifoldStream(Synthetic, Datastream, Seeded, Decoder, Generator):
	def generate(self, N: int): # generates observations
		return self.generate_observation_from_mechanism(self.generate_mechanism(N))


	@material.from_size('mechanism')
	def generate_mechanism(self, N: int):
		with self.force_rng(rng=self.rng):
			return self.space_of('mechanism').sample(N)


	@machine('observation')
	def generate_observation_from_mechanism(self, mechanism):
		raise NotImplementedError



class Deterministic(ManifoldStream, Decoder):
	@machine('observation')
	def generate_observation_from_mechanism(self, mechanism):
		return self.decode(mechanism)


	def decode(self, mechanism): # deterministic mapping from mechanism to observation
		raise NotImplementedError



class Distributional(ManifoldStream):
	def generate_observation_from_mechanism(self, mechanism):
		with self.force_rng(rng=self.rng): # TODO: change force to push
			return self.decode_distribution(mechanism).sample()


	def decode_distribution(self, mechanism):
		raise NotImplementedError



class Stochastic(Distributional, Deterministic):
	def _decode_distrib_from_mean(self, mean):
		raise NotImplementedError


	def decode_distribution(self, mechanism):
		return self._decode_distrib_from_mean(self.decode(mechanism))



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


	@space('mechanism')
	def mechanism_space(self):
		return spaces.Joint(
			spaces.Bound(min=self.tmin, max=self.tmax),
			spaces.Bound(min=0., max=1.),
		)


	@space('target')
	def target_space(self):
		return self.mechanism_space[0]


	@space('observation')
	def observation_space(self):
		# assert Ax > 0 and Ay > 0 and Az > 0 and freq > 0 and tmax > tmin, \
		# 	f'invalid parameters: {Ax} {Ay} {Az} {freq} {tmax} {tmin}'
		return spaces.Joint(
			spaces.Bound(min=-self.Ax * self.tmax, max=self.Ax * self.tmax),
			spaces.Bound(min=0., max=self.Ay),
			spaces.Bound(min=-self.Az * self.tmax, max=self.Az * self.tmax),
		)


	@machine('target')
	def get_target(self, mechanism):
		return mechanism.narrow(-1,0,1) #if self.target_theta else src['mechanism']


	def decode(self, mechanism):
		theta = mechanism.narrow(-1,0,1)
		height = mechanism.narrow(-1,1,1)

		pts = torch.cat([
			self.Ax * theta * theta.mul(self.freq*np.pi).cos(),
			self.Ay * height,
			self.Az * theta * theta.mul(self.freq*np.pi).sin(),
		], -1)
		return pts



@inherit_hparams('n_samples', 'Ax', 'Ay', 'Az', 'freq', 'tmin', 'tmax')
class SwissRollDataset(Sampledstream, SwissRoll):
	pass



class Helix(ManifoldStream):
	n_helix = hparam(2, space=spaces.Naturals())

	periodic_strand = hparam(False, space=spaces.Binary())

	Rx = hparam(1., space=spaces.HalfBound(min=0.))
	Ry = hparam(1., space=spaces.HalfBound(min=0.))
	Rz = hparam(1., space=spaces.HalfBound(min=0.))

	w = hparam(1., space=spaces.HalfBound(min=0.))


	@space('mechanism')
	def mechanism_space(self):
		return spaces.Joint(
			spaces.Periodic(min=-1., max=1.) if self.periodic_strand else spaces.Bound(min=-1., max=1.),
			spaces.Categorical(n=self.n_helix),
		)


	@space('target')
	def target_space(self):
		return self.mechanism_space[-1]


	@space('observation')
	def observation_space(self):
		return spaces.Joint(
			spaces.Bound(min=-self.Rx, max=self.Rx),
			spaces.Bound(min=-self.Ry, max=self.Ry),
			spaces.Bound(min=-self.Rz, max=self.Rz),
		)


	@machine('target')
	def get_target(self, mechanism):
		return mechanism.narrow(-1,1,1).long()


	def decode(self, mechanism):
		z = mechanism.narrow(-1, 0, 1)
		n = mechanism.narrow(-1, 1, 1)
		theta = z.mul(self.w).add(n.div(self.n_helix) * 2).mul(np.pi)

		amp = torch.as_tensor([self.Rx, self.Ry, self.Rz]).float().to(n.device)
		pts = amp.unsqueeze(0) * torch.cat([theta.cos(), theta.sin(), z], -1)
		return pts



@inherit_hparams('n_samples', 'n_helix', 'periodic_strand', 'Rx', 'Ry', 'Rz', 'w')
class HelixDataset(Sampledstream, Helix):
	pass



