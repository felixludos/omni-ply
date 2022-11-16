import numpy as np
# from sklearn.datasets import make_swiss_roll
import torch
from omnibelt import unspecified_argument

# from ..flavors import SyntheticDataset
from ..materials import Materialed, material
from ...parameters import hparam, inherit_hparams, Buildable
from ...structure import spaces, Decoder, Generator, NormalDistribution
from ...features import Seeded

from ..flavors import Synthetic
from ..common import Datastream


class ManifoldStream(Materialed, Synthetic, Datastream, Seeded, Decoder, Generator):
	class Batch(Synthetic, Datastream.Batch):
		pass
	class View(Synthetic, Datastream.View):
		pass

	# @material('target')
	@material('mechanism')
	def get_mechanism(self, src):
		return self.generate_mechanism(src.size)

	@material('observation')
	def get_observation(self, src):
		return self.generate_observation_from_mechanism(src['mechanism'])


	def generate(self, N): # generates observations
		return self.generate_observation_from_mechanism(self.generate_mechanism(N))

	def generate_mechanism(self, N):
		return self.space_of('mechanism').sample(N, gen=self.gen)

	def generate_observation_from_mechanism(self, mechanism):
		return self.decode(mechanism)

	def decode(self, mechanism):
		raise NotImplementedError



class Stochastic(ManifoldStream):
	def generate_observation_from_mechanism(self, mechanism):
		return self.decode_distrib(mechanism).sample()

	def _decode_distrib_from_mean(self, mean):
		raise NotImplementedError

	def decode_distrib(self, mechanism):
		return self._decode_distrib_from_mean(self.decode(mechanism))



class Noisy(Stochastic):
	def __init__(self, noise_std=0., **kwargs):
		super().__init__(**kwargs)
		self.noise_std = noise_std

	def _decode_distrib_from_mean(self, mean):
		return NormalDistribution(mean, self.noise_std * torch.ones_like(mean))



class SwissRoll(ManifoldStream):
	def __init__(self, *, Ax=np.pi/2, Ay=21., Az=np.pi/2, freq=0.5, tmin=3., tmax=9., **kwargs):
		super().__init__(**kwargs)

		assert Ax > 0 and Ay > 0 and Az > 0 and freq > 0 and tmax > tmin, \
			f'invalid parameters: {Ax} {Ay} {Az} {freq} {tmax} {tmin}'
		self.Ax, self.Ay, self.Az = Ax, Ay, Az
		self.freq = freq
		self.tmin, self.tmax = tmin, tmax

		# self.target_theta = target_theta

		mechanism_space = spaces.Joint(
			spaces.Bound(min=tmin, max=tmax),
			spaces.Bound(min=0., max=1.),
		)
		self.mechanism_space = mechanism_space
		# self.target_space = lbl_space[0] #if self.target_theta else lbl_space

		obs_space = spaces.Joint(
			spaces.Bound(min=-Ax * tmax, max=Ax * tmax),
			spaces.Bound(min=0., max=self.Ay),
			spaces.Bound(min=-Az * tmax, max=Az * tmax),
		)
		self.observation_space = obs_space


	def decode(self, mechanism):
		theta = mechanism.narrow(-1,0,1)
		height = mechanism.narrow(-1,1,1)

		pts = torch.cat([
			self.Ax * theta * theta.mul(self.freq*np.pi).cos(),
			self.Ay * height,
			self.Az * theta * theta.mul(self.freq*np.pi).sin(),
		], -1)
		return pts



class Helix(ManifoldStream):
	def __init__(self, n_helix=2, *, periodic_strand=False, Rx=1., Ry=1., Rz=1., w=1., **kwargs):
		super().__init__(**kwargs)

		self.n_helix = n_helix
		# self.target_strand = target_strand

		self.Rx, self.Ry, self.Rz = Rx, Ry, Rz
		self.w = int(w) if periodic_strand else w

		mechanism_space = spaces.Joint(
			spaces.Periodic(min=-1., max=1.) if periodic_strand else spaces.Bound(min=-1., max=1.),
			spaces.Categorical(n=n_helix),
		)
		self.mechanism_space = mechanism_space
		# self.target_space = lbl_space[-1] #if self.target_strand else lbl_space

		obs_space = spaces.Joint(
			spaces.Bound(min=-Rx, max=Rx),
			spaces.Bound(min=-Ry, max=Ry),
			spaces.Bound(min=-Rz, max=Rz),
		)
		self.observation_space = obs_space


	def decode(self, mechanism):
		z = mechanism.narrow(-1, 0, 1)
		n = mechanism.narrow(-1, 1, 1)
		theta = z.mul(self.w).add(n.div(self.n_helix) * 2).mul(np.pi)

		amp = torch.as_tensor([self.Rx, self.Ry, self.Rz]).float().to(n.device)
		pts = amp.unsqueeze(0) * torch.cat([theta.cos(), theta.sin(), z], -1)
		return pts



class SimpleSwissRoll(SwissRoll):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.target_space = self.mechanism_space[0]

	@material('target')
	def get_target(self, src):
		return src['mechanism'].narrow(-1,0,1) #if self.target_theta else src['mechanism']



class SimpleHelix(Helix):
	def __init__(self, n_helix=2, **kwargs):
		super().__init__(n_helix=n_helix, **kwargs)
		self.target_space = self.mechanism_space[-1]


	@material('target')
	def get_target(self, src):
		return src['mechanism'].narrow(-1,1,1).long() #if self.target_strand else src['mechanism']





