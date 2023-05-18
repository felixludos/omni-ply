import numpy as np
# import torch
from omnibelt import unspecified_argument, agnostic
# from sklearn.datasets import make_swiss_roll

# from ..materials import Materialed, material
from ...structure import spaces, Decoder, Generator, NormalDistribution
from ...features import Seeded
from ...parameters import submodule, hparam, inherit_hparams
from ...tools import material, machine, space

from ..flavors import Synthetic, Sampledstream, SimpleSampledStream
from ..top import Datastream



class ManifoldStream(Datastream, Seeded, Generator):
	def generate(self, N: int): # generates observations
		return self.generate_observation_from_manifold(self.sample_manifold(N))


	@material.from_size('manifold')
	def sample_manifold(self, N: int):
		return self.space_of('manifold').sample(N)


	@property
	def manifold_space(self):
		return self.space_of('manifold')


	@machine('observation')
	def generate_observation_from_manifold(self, manifold):
		raise NotImplementedError



class DeterministicManifold(ManifoldStream, Decoder):
	def generate_observation_from_manifold(self, manifold):
		return self.decode(manifold)


	def decode(self, manifold): # deterministic mapping from manifold to observation
		raise NotImplementedError



class DistributionalManifold(ManifoldStream):
	def generate_observation_from_manifold(self, manifold):
		with self.force_rng(rng=self.rng): # TODO: change force to push
			return self.decode_distribution(manifold).sample()


	def decode_distribution(self, manifold):
		raise NotImplementedError



class NoisyManifold(DistributionalManifold, DeterministicManifold):
	def _decode_distrib_from_mean(self, mean):
		raise NotImplementedError


	def decode_distribution(self, manifold):
		return self._decode_distrib_from_mean(self.decode(manifold))



class Noisy(NoisyManifold):
	noise_std = hparam(0.1, space=spaces.HalfBound(min=0.))


	def _decode_distrib_from_mean(self, mean):
		return NormalDistribution(mean, self.noise_std * torch.ones_like(mean))



####################################################################################################



class SwissRoll(DeterministicManifold):
	Ax = hparam(np.pi / 2, space=spaces.HalfBound(min=0.))
	Ay = hparam(21., space=spaces.HalfBound(min=0.))
	Az = hparam(np.pi / 2, space=spaces.HalfBound(min=0.))

	freq = hparam(0.5, space=spaces.HalfBound(min=0.))
	tmin = hparam(3., space=spaces.HalfBound(min=0.))
	tmax = hparam(9., space=spaces.HalfBound(min=0.))


	@space('manifold')
	def manifold_space(self):
		return spaces.Joint(
			spaces.Bound(min=self.tmin, max=self.tmax),
			spaces.Bound(min=0., max=1.),
		)


	@space('target')
	def target_space(self):
		return self.manifold_space[0]


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
	def get_target(self, manifold):
		return manifold.narrow(-1,0,1) #if self.target_theta else manifold


	def decode(self, manifold):
		theta = manifold.narrow(-1,0,1)
		height = manifold.narrow(-1,1,1)

		pts = torch.cat([
			self.Ax * theta * theta.mul(self.freq*np.pi).cos(),
			self.Ay * height,
			self.Az * theta * theta.mul(self.freq*np.pi).sin(),
		], -1)
		return pts



class Helix(DeterministicManifold):
	n_helix = hparam(2, space=spaces.Naturals())

	periodic_strand = hparam(False, space=spaces.Binary())

	Rx = hparam(1., space=spaces.HalfBound(min=0.))
	Ry = hparam(1., space=spaces.HalfBound(min=0.))
	Rz = hparam(1., space=spaces.HalfBound(min=0.))

	w = hparam(1., space=spaces.HalfBound(min=0.))


	@space('manifold')
	def manifold_space(self):
		return spaces.Joint(
			spaces.Periodic(min=-1., max=1.) if self.periodic_strand else spaces.Bound(min=-1., max=1.),
			spaces.Categorical(n=self.n_helix),
		)


	@space('target')
	def target_space(self):
		return self.manifold_space[-1]


	@space('observation')
	def observation_space(self):
		return spaces.Joint(
			spaces.Bound(min=-self.Rx, max=self.Rx),
			spaces.Bound(min=-self.Ry, max=self.Ry),
			spaces.Bound(min=-self.Rz, max=self.Rz),
		)


	@machine('target')
	def get_target(self, manifold):
		return manifold.narrow(-1,1,1).long()


	def decode(self, manifold):
		z = manifold.narrow(-1, 0, 1)
		n = manifold.narrow(-1, 1, 1)
		theta = z.mul(self.w).add(n.div(self.n_helix) * 2).mul(np.pi)

		amp = torch.as_tensor([self.Rx, self.Ry, self.Rz]).float().to(n.device)
		pts = amp.unsqueeze(0) * torch.cat([theta.cos(), theta.sin(), z], -1)
		return pts



@inherit_hparams('n_samples')
class SwissRollDataset(SimpleSampledStream, source_cls=SwissRoll):
	pass



@inherit_hparams('n_samples')
class HelixDataset(SimpleSampledStream, source_cls=Helix):
	pass


