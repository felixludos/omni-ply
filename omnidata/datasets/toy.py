import numpy as np
# from sklearn.datasets import make_swiss_roll
import torch

from .base import SyntheticDataset
from ..framework import spaces


class SwissRollDataset(SyntheticDataset):
	def __init__(self, n_samples=100, noise=0., target_theta=True,
	             Ax=np.pi/2, Ay=21., Az=np.pi/2, freq=0.5, tmin=3., tmax=9.,
	             **kwargs):
		super().__init__(default_len=n_samples, **kwargs)

		# self.n_samples = n_samples
		self.noise_std = noise

		assert Ax > 0 and Ay > 0 and Az > 0 and freq > 0 and tmax > tmin, f'invalid parameters: ' \
		                                                                  f'{Ax} {Ay} {Az} {freq} {tmax} {tmin}'
		self.Ax, self.Ay, self.Az = Ax, Ay, Az
		self.freq = freq
		self.tmin, self.tmax = tmin, tmax

		self._target_theta = target_theta

		lbl_space = spaces.Joint(
			spaces.Bound(min=tmin, max=tmax),
			spaces.Bound(min=0., max=1.),
		)

		obs_space = spaces.Joint(
			spaces.Bound(min=-Ax * tmax, max=Ax * tmax),
			spaces.Bound(min=0., max=self.Ay),
			spaces.Bound(min=-Az * tmax, max=Az * tmax),
		)

		self.register_buffer('observation', space=obs_space)
		if self._target_theta:
			self.register_buffer('target', space=lbl_space[0])
		self.register_buffer('label', space=lbl_space)


	def _generate_noise(self, N, seed=None, gen=None):
		if seed is not None:
			gen = torch.Generator().manual_seed(seed)
		if gen is None:
			gen = self.gen
		return self.noise_std * torch.randn(N, 3, generator=gen)


	def generate_observation_from_mechanism(self, mechanism, seed=None, gen=None):
		theta = mechanism.narrow(-1,0,1)
		height = mechanism.narrow(-1,1,1)

		pts = torch.cat([
			self.Ax * theta * theta.mul(self.freq*np.pi).cos(),
			self.Ay * height,
			self.Az * theta * theta.mul(self.freq*np.pi).sin(),
		], -1) + self._generate_noise(len(theta), seed=seed, gen=gen)
		return pts


	def _prepare(self, *args, **kwargs):
		lbls = self.generate_mechanism(len(self))

		self.buffers['label'].data = lbls
		if self._target_theta:
			self.buffers['target'].data = lbls.narrow(-1,0,1)
		self.buffers['observation'].data = self.generate_observation_from_mechanism(lbls)

		super()._prepare(*args, **kwargs)



class HelixDataset(SyntheticDataset):
	def __init__(self, n_samples=100, n_helix=2, noise=0.,
	             target_strand=False, periodic_strand=False,
	             Rx=1., Ry=1., Rz=1., w=1.,
	             **kwargs):
		super().__init__(default_len=n_samples, **kwargs)

		self.n_helix = n_helix
		self.noise_std = noise
		self._target_strand = target_strand

		self.Rx, self.Ry, self.Rz = Rx, Ry, Rz
		self.w = int(w) if periodic_strand else w

		lbl_space = spaces.Joint(
			spaces.Periodic(min=-1., max=1.) if periodic_strand else spaces.Bound(min=-1., max=1.),
			spaces.Categorical(n=n_helix),
		)

		obs_space = spaces.Joint(
			spaces.Bound(min=-Rx, max=Rx),
			spaces.Bound(min=-Ry, max=Ry),
			spaces.Bound(min=-Rz, max=Rz),
		)

		self.register_buffer('observation', space=obs_space)
		if self._target_strand:
			self.register_buffer('target', space=lbl_space[-1])
		self.register_buffer('label', space=lbl_space)


	def _generate_noise(self, N, seed=None, gen=None):
		if seed is not None:
			gen = torch.Generator().manual_seed(seed)
		if gen is None:
			gen = self.gen
		return self.noise_std * torch.randn(N, 3, generator=gen)


	def generate_observation_from_mechanism(self, mechanism, seed=None, gen=None):
		z = mechanism.narrow(-1, 0, 1)
		n = mechanism.narrow(-1, 1, 1)
		theta = z.mul(self.w).add(n.div(self.n_helix) * 2).mul(np.pi)

		amp = torch.as_tensor([self.Rx, self.Ry, self.Rz]).float().to(n.device)
		pts = amp.unsqueeze(0) * torch.cat([theta.cos(), theta.sin(), z], -1)
		return pts + self._generate_noise(len(theta), seed=seed, gen=gen)


	def _prepare(self, *args, **kwargs):
		lbls = self.generate_mechanism(len(self))

		self.buffers['label'].data = lbls
		if self._target_strand:
			self.buffers['target'].data = lbls.narrow(-1, 0, 1)
		self.buffers['observation'].data = self.generate_observation_from_mechanism(lbls)

		super()._prepare(*args, **kwargs)







