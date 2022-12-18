from omnibelt import agnostic, unspecified_argument
import os
import random
import numpy as np
import torch


def set_global_seed(seed=None):
	if seed is None:
		seed = Seeded.gen_random_seed()
	random.seed(seed)
	np.random.seed(seed)
	torch.manual_seed(seed)
	if torch.cuda.is_available():
		torch.cuda.manual_seed(seed)
	return seed


# def set_seed(seed: int = 42) -> None:
#     np.random.seed(seed)
#     random.seed(seed)
#     torch.manual_seed(seed)
#     torch.cuda.manual_seed(seed)
#     # When running on the CuDNN backend, two further options must be set
#     torch.backends.cudnn.deterministic = True
#     torch.backends.cudnn.benchmark = False
#     # Set a fixed value for the hash seed
#     os.environ["PYTHONHASHSEED"] = str(seed)
#     print(f"Random seed set as {seed}")

# def set_seed(seed: int = 42) -> None:
#   random.seed(seed)
#   np.random.seed(seed)
#   tf.random.set_seed(seed)
#   tf.experimental.numpy.random.seed(seed)
#   tf.set_random_seed(seed)
#   # When running on the CuDNN backend, two further options must be set
#   os.environ['TF_CUDNN_DETERMINISTIC'] = '1'
#   os.environ['TF_DETERMINISTIC_OPS'] = '1'
#   # Set a fixed value for the hash seed
#   os.environ["PYTHONHASHSEED"] = str(seed)
#   print(f"Random seed set as {seed}")






class Seeded:
	# shared_deterministic_seed = 16283393149723337453
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


	@agnostic
	def _gen_deterministic_seed(self, base_seed):
		return self.gen_random_seed(torch.Generator().manual_seed(base_seed))


	@agnostic
	def gen_random_seed(self, gen=None):
		if gen is None:
			gen = self.gen
		return torch.randint(-2**63, 2**63-1, size=(), generator=gen).item()


	@agnostic
	def create_rng(self, seed=None, base_gen=None):
		if seed is None:
			seed = self.gen_random_seed(base_gen)
		gen = torch.Generator()
		gen.manual_seed(seed)
		return gen


	@agnostic
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
	return Seeded._gen_deterministic_seed(base_seed)



def gen_random_seed(base_gen=None):
	return Seeded.gen_random_seed(base_gen)



def create_rng(seed=None, base_gen=None):
	return Seeded.create_rng(seed=seed, base_gen=base_gen)



# from .simple import Prepared

class RNGManager:

	# shared_deterministic_seed = 16283393149723337453
	def __init__(self, *args, master_seed=None, **kwargs):
		if master_seed is None:
			master_seed = self.gen_random_seed()
		super().__init__(*args, **kwargs)
		self._meta_rng = None
		self._prime_rngs = []  # TODO: push and pop prime using context manager
		self.master_seed = master_seed
		self.set_global_seed(self.master_seed)

	def push_prime(self, seed=None, base_gen=None):
		self._prime_rngs.append(self.create_rng(seed=seed, base_gen=base_gen))

	def pop_prime(self):
		self._prime_rngs.pop()

	@property
	def master_seed(self):
		return self._master_seed

	@master_seed.setter
	def master_seed(self, seed):
		self._master_seed = seed
		self._meta_rng = self.create_rng(seed=seed)


	def create_personal_rng(self, obj, seed=None):
		rng = self.create_rng(seed=seed, base_gen=self._meta_rng)
		obj._rng = rng
		return rng

	def get_personal_rng(self, obj):
		if len(self._prime_rngs):
			return self._prime_rngs[-1]

		personal = getattr(obj, '_rng', None)
		if personal is None:
			return self.create_personal_rng(obj)
		return personal

	def clear_personal_rng(self, obj):
		obj._rng = None


	@agnostic
	def create_rng(self, seed=None, base_gen=None):
		if seed is None:
			seed = self.gen_random_seed(base_gen)
		return self._create_rng(seed)

	@agnostic
	def _gen_deterministic_seed(self, base_seed):
		return self.gen_random_seed(self.create_rng(base_seed))

	@agnostic
	def gen_random_seed(self, gen=None) -> int:
		raise NotImplementedError

	def _create_rng(self, seed):
		raise NotImplementedError

	@agnostic
	def set_global_seed(self, seed):
		os.environ["PYTHONHASHSEED"] = str(seed)

		np.random.seed(seed)
		random.seed(seed)

	@agnostic
	def using_seed(self, seed=None, gen=None):
		return self.SeedContext(self, seed=seed, gen=gen)


	class SeedContext:
		def __init__(self, src=None, seed=None, gen=None):
			self.src = src
			self.seed = seed
			self.gen = gen


		def __enter__(self):
			if self.gen is None:
				self.gen = self.src.create_rng(seed=self.seed)
			self.src.push_prime(self.gen)
			return self.gen


		def __exit__(self, exc_type, exc_val, exc_tb):
			self.src.pop_prime()


# class NumpyManager(RNGManager):
# 	pass

# class TensorflowManager(RNGManager):
# 	pass

	# tf.random.set_seed(seed)
	# tf.experimental.numpy.random.seed(seed)
	# tf.set_random_seed(seed)
	# os.environ['TF_CUDNN_DETERMINISTIC'] = '1'
	# os.environ['TF_DETERMINISTIC_OPS'] = '1'


class PytorchManager(RNGManager):
	@agnostic
	def gen_random_seed(self, gen=None):
		return torch.randint(-2 ** 63, 2 ** 63 - 1, size=(), generator=gen).item()

	@agnostic
	def _create_rng(self, seed):
		gen = torch.Generator()
		gen.manual_seed(seed)
		return gen

	@agnostic
	def set_global_seed(self, seed):
		super().set_global_seed(seed)
		torch.manual_seed(seed)
		torch.cuda.manual_seed(seed)
		torch.backends.cudnn.deterministic = True
		torch.backends.cudnn.benchmark = False




class RNG: # descriptor
	Manager = PytorchManager

	manager = None

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.manager is None:
			self.__class__.manager = self.Manager()

	def __get__(self, obj, owner=None):
		return self.manager.choose_rng(obj)

	def reset(self, obj): # TODO
		self.manager.clear_personal_rng(obj)



class Seeded:
	_rng_type = RNG
	_seed = None

	def __init__(self, *args, rng=None, seed=unspecified_argument, **kwargs):
		if rng is None:
			rng = self._rng_type(seed)
		super().__init__(*args, **kwargs)
		if seed is not unspecified_argument:
			self._seed = seed
		self.rng = rng

	def get_rng(self):
		return self.__dict__.get('rng', None)

	def reset_rng(self, seed=unspecified_argument):
		if seed is not unspecified_argument:
			self._seed = seed
		self.get_rng().reset(self, seed=self._seed)

	@property
	def seed(self):
		return self._seed













