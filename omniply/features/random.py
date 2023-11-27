from omnibelt import agnostic, unspecified_argument
import os
import random
import inspect
import numpy as np
# import torch


class RNGManager:
	_fallback_rng_seed = 16283393149723337453
	def __init__(self, *args, master_seed=None, **kwargs):
		if master_seed is None:
			master_seed = self.gen_random_seed()
		super().__init__(*args, **kwargs)
		self._meta_rng = None
		self._forced_rngs = []
		self._default_rngs = []
		self.master_seed = master_seed
		self.set_global_seed(self.master_seed)

	def push_forced(self, seed=None, *, rng=None):
		if rng is None:
			rng = self.create_rng(seed=seed)
		self._forced_rngs.append(rng)
	def pop_forced(self):
		return self._forced_rngs.pop()

	def push_default(self, seed=None, *, rng=None):
		if rng is None:
			rng = self.create_rng(seed=seed)
		self._default_rngs.append(rng)
	def pop_default(self):
		return self._default_rngs.pop()

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
		if len(self._default_rngs):
			return self._default_rngs[0]

	def get_personal_rng(self, obj=None):
		if len(self._forced_rngs):
			return self._forced_rngs[-1]

		personal = getattr(obj, '_rng', None)
		if personal is None:
			return self.create_personal_rng(obj)
		return personal

	def replace_personal_rng(self, obj, *, rng=None, seed=unspecified_argument):
		if rng is None and seed is not unspecified_argument:
			rng = self.create_rng(seed=seed)
		obj._rng = rng
		return rng

	def clear_personal_rng(self, obj):
		self.replace_personal_rng(obj, rng=None)

	@agnostic
	def create_rng(self, seed=None, base_gen=None):
		if seed is None:
			seed = self.gen_random_seed(base_gen)
		return self._create_rng(seed)

	@agnostic
	def gen_deterministic_seed(self, base_seed):
		return self.gen_random_seed(self.create_rng(base_seed))

	@agnostic
	def gen_random_seed(self, gen=None) -> int:
		raise NotImplementedError

	def _create_rng(self, seed):
		raise NotImplementedError

	def set_global_seed(self, seed):
		os.environ["PYTHONHASHSEED"] = str(seed)

		np.random.seed(seed % (2**32))
		random.seed(seed)

	def force_rng(self, seed=unspecified_argument, *, rng=None):
		if seed is not unspecified_argument or rng is not None:
			return self.SeedContext(self.push_forced, self.pop_forced, self, seed=seed, rng=rng)

	def default_rng(self, seed=unspecified_argument, *, rng=None):
		if seed is not unspecified_argument or rng is not None:
			return self.SeedContext(self.push_default, self.pop_default, self, seed=seed, rng=rng)

	class SeedContext:
		def __init__(self, push, pop, src=None, seed=None, rng=None):
			self.push = push
			self.pop = pop
			self.src = src
			self.seed = seed
			self.rng = rng

		def __enter__(self):
			if self.rng is None:
				self.rng = self.src.create_rng(seed=self.seed)
			self.push(rng=self.rng)
			return self.rng

		def __exit__(self, exc_type, exc_val, exc_tb):
			self.pop()


import numpy as np

class PytorchManager(RNGManager):
	@agnostic
	def gen_random_seed(self, gen=None):
		if gen is None:
			gen = np.random
		return gen.randint(0, 2**30)#.item()
		# return torch.randint(-2 ** 63, 2 ** 63 - 1, size=(), generator=gen).item()

	@agnostic
	def _create_rng(self, seed):
		# gen = torch.Generator()
		# gen.manual_seed(seed)
		gen = np.random.RandomState(seed)
		return gen

	@agnostic
	def set_global_seed(self, seed):
		super().set_global_seed(seed)
		np.random.seed(seed)
		# torch.manual_seed(seed)
		# torch.cuda.manual_seed(seed)
		# torch.backends.cudnn.deterministic = True
		# torch.backends.cudnn.benchmark = False


# class NumpyManager(RNGManager):
# 	pass

# class TensorflowManager(RNGManager):
# 	pass

	# tf.random.set_seed(seed)
	# tf.experimental.numpy.random.seed(seed)
	# tf.set_random_seed(seed)
	# os.environ['TF_CUDNN_DETERMINISTIC'] = '1'
	# os.environ['TF_DETERMINISTIC_OPS'] = '1'


default_rng_manager = PytorchManager()


def force_rng(seed=unspecified_argument, *, rng=None):
	return default_rng_manager.force_rng(seed=seed, rng=rng)


def default_rng(seed=unspecified_argument, *, rng=None):
	return default_rng_manager.default_rng(seed=seed, rng=rng)


def gen_deterministic_seed(base_seed):
	return default_rng_manager.gen_deterministic_seed(base_seed)


def gen_random_seed(base_gen=None):
	return default_rng_manager.gen_random_seed(base_gen)


def create_rng(seed=None, base_gen=None):
	return default_rng_manager.create_rng(seed=seed, base_gen=base_gen)


def set_global_seed(seed):
	return default_rng_manager.set_global_seed(seed)



class RNG_Base: # descriptor
	Manager = PytorchManager

	manager = default_rng_manager

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.manager is None:
			self.__class__.manager = self.Manager()

	def reset(self, obj): # TODO
		self.manager.clear_personal_rng(obj)
		return self.manager.get_personal_rng(obj)

	def force_rng(self, seed=unspecified_argument, *, rng=None):
		return self.manager.force_rng(seed=seed, rng=rng)

	def default_rng(self, seed=unspecified_argument, *, rng=None):
		return self.manager.default_rng(seed=seed, rng=rng)

	def get_default_rng(self):
		return self.manager.get_default_rng()

	def gen_deterministic_seed(self, base_seed):
		return self.manager.gen_deterministic_seed(base_seed)

	def gen_random_seed(self, base_gen=None):
		return self.manager.gen_random_seed(base_gen)



class RNG(RNG_Base):
	def __get__(self, obj, owner=None):
		return self.manager.get_personal_rng(obj)

	def __set__(self, obj, value):
		self.manager.replace_personal_rng(obj, rng=value)



class RNG_Link(RNG_Base):
	def __get__(self, obj, owner=None):
		return self.manager.get_default_rng()

	def __set__(self, obj, value):
		pass



class Seedable: # has no rng of its own, but respects forced rngs
	rng = RNG_Link()
	_seed = None

	def __init__(self, *args, rng=unspecified_argument, seed=unspecified_argument, **kwargs):
		super().__init__(*args, **kwargs)
		if seed is not unspecified_argument:
			self._seed = seed
		if rng is not unspecified_argument:
			self.rng = rng

	def default_rng(self, seed=unspecified_argument, *, rng=None):
		if rng is None:
			rng = self.rng
		return self._get_rng().default_rng(seed=seed, rng=rng)

	def force_rng(self, seed=unspecified_argument, *, rng=None):
		if rng is None:
			rng = self.rng
		return self._get_rng().force_rng(seed=seed, rng=rng)

	@classmethod
	def _get_rng(cls):
		return inspect.getattr_static(cls, 'rng', None)

	def reset_rng(self, seed=unspecified_argument):
		if seed is not unspecified_argument:
			self._seed = seed
		return self._get_rng().reset(self)

	@property
	def seed(self):
		return self._seed



class Seeded(Seedable): # uses its own RNG unless one is forced
	rng = RNG() # access only when needed (rather than passing as argument)




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











