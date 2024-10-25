from .imports import *



class BatchRNG(ToolKit):
	def __init__(self, seed: int = None, **kwargs):
		super().__init__(**kwargs)
		self._seed = seed

	# @tool('seed')
	# def get_seed(self, epoch_seed: int = None, epoch_offset: int = None) -> int:
	# 	return int(hashlib.md5(f'{epoch_seed},{epoch_offset}'.encode()).hexdigest(), 16) % (2**32)

	@tool('seed')
	def get_seed(self, drawn_batches: int) -> int:
		return int(hashlib.md5(f'{self._seed},{drawn_batches}'.encode()).hexdigest(), 16) % (2**32)


