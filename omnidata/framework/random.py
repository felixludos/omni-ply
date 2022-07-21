
from omnibelt import agnosticmethod
import torch

from . import abstract


def set_seed(seed=None):
	if seed is None:
		seed = Seeded.gen_random_seed()
	# random.seed(seed)
	# np.random.seed(seed)
	torch.manual_seed(seed)
	if torch.cuda.is_available():
		torch.cuda.manual_seed(seed)
	return seed



class Seeded:
	_seed = None
	gen = None

	def __init__(self, *args, gen=None, seed=None, **kwargs):
		super().__init__(*args, **kwargs)
		if gen is not None:
			self.gen = gen
		if seed is None:
			self._seed = seed
		else:
			self.seed = seed


	@property
	def seed(self):
		return self._seed
	@seed.setter
	def seed(self, seed):
		# if seed is None:
		# 	seed = self.gen_random_seed(self.gen)
		self._seed = seed
		self.gen = self.create_rng(seed=seed)


	# @agnosticmethod
	# def get_master_gen(self):


	@agnosticmethod
	def gen_deterministic_seed(self, base_seed):
		return self.gen_random_seed(torch.Generator().manual_seed(base_seed))


	@agnosticmethod
	def gen_random_seed(self, gen=None):
		if gen is None:
			gen = self.gen
		return torch.randint(-2**63, 2**63-1, size=(), generator=gen).item()


	@agnosticmethod
	def create_rng(self, seed=None, base_gen=None):
		if seed is None:
			seed = self.gen_random_seed(base_gen)
		gen = torch.Generator()
		gen.manual_seed(seed)
		return gen


	@agnosticmethod
	def using_rng(self, seed=None, gen=None, src=None):
		if src is None:
			src = Seeded
		return self.SeedContext(src=src, seed=seed, gen=gen)


	class SeedContext:
		def __init__(self, src=None, seed=None, gen=None):
			self.src = src
			self.seed = seed
			self.gen = gen


		def __enter__(self):
			gen = self.src.create_rng(seed=self.seed, base_gen=self.gen)
			self.prev = self.src.gen
			self.src.gen = gen
			return gen


		def __exit__(self, exc_type, exc_val, exc_tb):
			self.src.gen = self.prev



def using_rng(seed=None, gen=None, src=None):
	return Seeded.using_rng(seed=seed, gen=gen, src=src)



def gen_deterministic_seed(base_seed):
	return Seeded.gen_deterministic_seed(base_seed)



def gen_random_seed(base_gen=None):
	return Seeded.gen_random_seed(base_gen)



def create_rng(seed=None, base_gen=None):
	return Seeded.create_rng(seed=seed, base_gen=base_gen)



class Sampler(Seeded, abstract.Generator):
	def sample(self, *shape, gen=None, **kwargs):
		if gen is None:
			gen = self.gen
		return self._sample(torch.Size(shape), gen=gen, **kwargs)


	def _sample(self, shape, gen, **kwargs):
		raise NotImplementedError

