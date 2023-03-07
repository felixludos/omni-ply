from omnibelt import agnostic, unspecified_argument
import os
import random
import inspect
import numpy as np
import torch


class RNGManager:

	# shared_deterministic_seed = 16283393149723337453
	def __init__(self, *args, master_seed=None, **kwargs):
		if master_seed is None:
			master_seed = self.gen_random_seed()
		super().__init__(*args, **kwargs)
		self._meta_rng = None
		self._prime_rngs = []  # TODO: push and pop prime using context manager
		self._default_rng = None
		self.master_seed = master_seed
		self.set_global_seed(self.master_seed)
		self.get_default_rng()

	def push_prime(self, seed=None, *, rng=None):
		if rng is None:
			rng = self.create_rng(seed=seed)
		self._prime_rngs.append(rng)

	def pop_prime(self):
		return self._prime_rngs.pop()

	@property
	def master_seed(self):
		return self._master_seed

	@master_seed.setter
	def master_seed(self, seed):
		self._master_seed = seed
		self._meta_rng = self.create_rng(seed=seed)


	def create_personal_rng(self, obj, seed=unspecified_argument):
		if seed is unspecified_argument:
			seed = getattr(obj, '_seed', None)
		rng = self.create_rng(seed=seed, base_gen=self._meta_rng)
		obj._rng = rng
		return rng

	def get_default_rng(self):
		if self._default_rng is None:
			self._default_rng = self.create_rng()
		return self._default_rng

	def get_personal_rng(self, obj=None):
		if len(self._prime_rngs):
			return self._prime_rngs[-1]
		if obj is None:
			return self.get_default_rng()

		personal = getattr(obj, '_rng', None)
		if personal is None:
			return self.create_personal_rng(obj)
		return personal

	def replace_personal_rng(self, obj, *, rng=None, seed=unspecified_argument):
		if rng is None and seed is not unspecified_argument:
			rng = self.create_rng(seed=seed)
		obj._rng = rng

	def clear_personal_rng(self, obj):
		self.replace_personal_rng(obj, rng=None)


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

		np.random.seed(seed % (2**32))
		random.seed(seed)

	@agnostic
	def force_rng(self, seed=unspecified_argument, *, rng=None):
		if seed is not unspecified_argument or rng is not None:
			return self.SeedContext(self, seed=seed, rng=rng)


	def set_default_rng(self, rng=None):
		old = self._default_rng
		self._default_rng = rng
		return old


	class SeedContext:
		def __init__(self, src=None, seed=None, rng=None):
			self.src = src
			self.seed = seed
			self.rng = rng


		def __enter__(self):
			if self.rng is None:
				self.rng = self.src.create_rng(seed=self.seed)
			self.src.push_prime(rng=self.rng)
			return self.rng


		def __exit__(self, exc_type, exc_val, exc_tb):
			self.src.pop_prime()



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


# class NumpyManager(RNGManager):
# 	pass

# class TensorflowManager(RNGManager):
# 	pass

	# tf.random.set_seed(seed)
	# tf.experimental.numpy.random.seed(seed)
	# tf.set_random_seed(seed)
	# os.environ['TF_CUDNN_DETERMINISTIC'] = '1'
	# os.environ['TF_DETERMINISTIC_OPS'] = '1'


default_rng_manager_type = PytorchManager


def force_rng(seed=unspecified_argument, *, rng=None):
	return default_rng_manager_type.force_rng(seed=seed, rng=rng)


def set_default_rng(rng):
	return default_rng_manager_type.set_default_rng(rng=rng)


def gen_deterministic_seed(base_seed):
	return default_rng_manager_type._gen_deterministic_seed(base_seed)


def gen_random_seed(base_gen=None):
	return default_rng_manager_type.gen_random_seed(base_gen)


def create_rng(seed=None, base_gen=None):
	return default_rng_manager_type.create_rng(seed=seed, base_gen=base_gen)


def set_global_seed(seed):
	return default_rng_manager_type.set_global_seed(seed)



class RNG: # descriptor
	Manager = PytorchManager

	manager = None

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.manager is None:
			self.__class__.manager = self.Manager()

	def __get__(self, obj, owner=None):
		return self.manager.get_personal_rng(obj)

	def __set__(self, obj, value):
		self.manager.replace_personal_rng(obj, rng=value)

	def reset(self, obj): # TODO
		self.manager.clear_personal_rng(obj)

	def force_rng(self, seed=unspecified_argument, *, rng=None):
		return self.manager.force_rng(seed=seed, rng=rng)

	def get_default_rng(self):
		return self.manager.get_default_rng()

	def set_default_rng(self, rng=None):
		return self.manager.set_default_rng(rng=rng)



class RNG_Link(RNG):
	def __get__(self, obj, owner=None):
		return self.manager.get_default_rng()



class Seeded: # uses its own RNG unless one is forced
	rng = RNG() # access only when needed (rather than passing as argument)
	_seed = None

	def __init__(self, *args, rng=unspecified_argument, seed=unspecified_argument, **kwargs):
		super().__init__(*args, **kwargs)
		if seed is not unspecified_argument:
			self._seed = seed
		if rng is not unspecified_argument:
			self.rng = rng

	def force_rng(self, seed=unspecified_argument, *, rng=None):
		return self._get_rng().force_rng(seed=seed, rng=rng)

	def set_default_rng(self, rng=None):
		return self._get_rng().set_default_rng(rng=rng)

	@classmethod
	def _get_rng(cls):
		return inspect.getattr_static(cls, 'rng', None)

	def reset_rng(self, seed=unspecified_argument):
		if seed is not unspecified_argument:
			self._seed = seed
		self._get_rng().reset(self)

	@property
	def seed(self):
		return self._seed



class Seedable(Seeded): # has no rng of its own, but respects forced rngs
	rng = RNG_Link()



# def set_global_seed(seed=None):
# 	if seed is None:
# 		seed = Seeded.gen_random_seed()
# 	random.seed(seed)
# 	np.random.seed(seed)
# 	torch.manual_seed(seed)
# 	if torch.cuda.is_available():
# 		torch.cuda.manual_seed(seed)
# 	return seed


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











