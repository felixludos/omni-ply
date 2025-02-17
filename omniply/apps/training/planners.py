from .imports import *
from .abstract import AbstractDataset, AbstractBatch, AbstractPlanner



class InfiniteUnindexed(AbstractPlanner):
	def __init__(self, src: AbstractDataset, **kwargs):
		super().__init__(src=src, **kwargs)
		self._dataset_size = src.size
		self._num_iterations = 0
		self._drawn_samples = 0
		self._drawn_batches = 0


	def step(self, size: int) -> Dict[str, Any]:
		info = super().step(size)
		self._num_iterations += 1
		return info
		

	def draw(self, n: int) -> Dict[str, Any]:
		self._drawn_batches += 1
		self._drawn_samples += n
		return {'size': n, 
				'num_iterations': self._num_iterations,
				'drawn_batches': self._drawn_batches, 
				'drawn_samples': self._drawn_samples}


	def generate(self, step_size: int) -> Iterator[Dict[str, Any]]:
		while True:
			yield self.step(step_size)


	def expected_iterations(self, step_size):
		return None



class InfiniteIndexed(InfiniteUnindexed):
	def __init__(self, src: AbstractDataset, *, shuffle: bool = True,
			  	 multi_epoch: bool = True, seed: int = None, sort_indices: bool = True,
				 **kwargs):
		if seed is None:
			seed = random.randint(1, 2**32-1)
		super().__init__(src=src, **kwargs)
		self._shuffle = shuffle
		self._multi_epoch = multi_epoch
		self._sort_indices = sort_indices
		self._seed = seed
		self._initial_seed = seed
		self._order = None
		self._offset = 0
		self._drawn_epochs = 0


	@staticmethod
	def _increment_seed(seed: int) -> int:
		'''deterministically change the seed'''
		return random.Random(seed).randint(1, 2**32-1)


	def _draw_indices(self, n: int):
		import numpy as np

		if self._dataset_size is None:
			return None

		if self._order is None:
			if self._drawn_samples > 0:
				self._seed = self._increment_seed(self._seed)
			self._order = np.random.RandomState(self._seed).permutation(self._dataset_size) if self._shuffle else np.arange(self._dataset_size)
			self._offset = 0
			self._drawn_epochs += 1

		assert self._multi_epoch or n < len(self._order), f'batch size is too large: max is {len(self._order)}'

		if self._offset + n > len(self._order): # need to wrap around
			indices = self._order[self._offset:]
			self._order = None
			if self._multi_epoch:
				indices = np.concatenate((indices, self._draw_indices(n - len(indices))))
		else:
			indices = self._order[self._offset:self._offset + n]
			self._offset += n
		
		if self._sort_indices:
			indices.sort()
		return indices

	
	def draw(self, n: int) -> Dict[str, Any]:
		assert n > 0, 'cannot draw zero samples' # otherwise some batches can have degenerate seeds
		seed = self._seed
		offset = self._offset
		idx = self._draw_indices(n)
		info = super().draw(n)
		if idx is not None:
			info.update({'index': idx, 'epochs': self._drawn_epochs, 
				'initial_seed': self._initial_seed, 'epoch_seed': seed, 'epoch_offset': offset})
		return info
	


class BudgetExceeded(Exception):
	pass



class Unindexed(InfiniteUnindexed):
	_BudgetExceeded = BudgetExceeded

	def __init__(self, src: AbstractDataset, *, max_samples: int = None, max_batches: int = None,
				 hard_budget: bool = False, drop_last: bool = True, 
				 max_iterations: int = None, **kwargs):
		'''
		:param hard_budget: if True, raise BudgetExceeded before drawing the batch that exceeds the budget, otherwise raise in the next draw
		:param drop_last: if True, drop the last batch if the last batch partially exceeds the budget, otherwise return the partial batch (only has an effect if hard_budget is False) (note: the only way for the draw to return a different number of samples than requested is if drop_last is False)
		'''
		super().__init__(src=src, **kwargs)
		assert max_samples is None or max_samples > 0, 'max_samples must be positive'
		assert max_batches is None or max_batches > 0, 'max_batches must be positive'
		assert max_iterations is None or max_iterations > 0, 'max_iterations must be positive'
		self._max_samples = max_samples
		self._max_batches = max_batches
		self._max_iterations = max_iterations

		self._hard_budget = hard_budget
		self._drop_last = drop_last

	def remaining_samples(self) -> Optional[int]:
		return self._max_samples - self._drawn_samples if self._max_samples is not None else None
	
	def remaining_batches(self) -> Optional[int]:
		return self._max_batches - self._drawn_batches if self._max_batches is not None else None
	
	def remaining_iterations(self) -> Optional[int]:
		return self._max_iterations - self._num_iterations if self._max_iterations is not None else None


	def step(self, batch_size: int) -> Dict[str, Any]:
		if self._max_iterations is not None and self._num_iterations >= self._max_iterations:
			raise self._BudgetExceeded(f'max iterations reached: {self._max_iterations}')
		return super().step(batch_size)
	

	def draw(self, n: int):
		if self._max_samples is not None and self._drawn_samples + n > self._max_samples:
			if self._drawn_samples >= self._max_samples or (self._hard_budget and self._drop_last):
				raise self._BudgetExceeded(f'max samples exceeded: {self._max_samples}')
			elif not self._hard_budget:
				pass # allow the draw to happen and raise in the next draw
			elif not self._drop_last:
				n = self._max_samples - self._drawn_samples
		if self._max_batches is not None and self._drawn_batches + 1 > self._max_batches:
			raise self._BudgetExceeded(f'max batches exceeded: {self._max_batches}')
		return super().draw(n)


	def generate(self, step_size: int) -> Iterator[Dict[str, Any]]:
		try:
			yield from super().generate(step_size)
		except BudgetExceeded:
			pass


	def expected_iterations(self, step_size: int) -> Optional[int]:
		if self._max_iterations is not None:
			return self._max_iterations - self._num_iterations
		if self._max_batches is not None:
			batches_per_iteration = (self._drawn_batches // self._num_iterations) if self._num_iterations > 0 else 1
			return (self._max_batches - self._drawn_batches) * batches_per_iteration
		if self._max_samples is not None:
			remaining = self._max_samples - self._drawn_samples
			return (remaining // step_size) + (1 if (remaining % step_size > 0 and not (self._hard_budget and self._drop_last)) else 0)
		return None
		


class Indexed(Unindexed, InfiniteIndexed):
	def __init__(self, src: AbstractDataset, *, max_epochs: int = None, **kwargs):
		super().__init__(src=src, **kwargs)
		assert max_epochs is None or max_epochs > 0, 'max_epochs must be positive'
		self._max_epochs = max_epochs


	def remaining_epochs(self) -> Optional[int]:
		return self._max_epochs - self._drawn_epochs if self._max_epochs is not None else None


	def draw(self, n: int):
		if self._max_epochs is not None and self._drawn_epochs >= self._max_epochs:
			assert self._dataset_size is not None, 'dataset size must be provided to draw the last batch'
			if self._drawn_epochs > self._max_epochs or self._offset == self._dataset_size:
				raise self._BudgetExceeded(f'max epochs exceeded: {self._max_epochs}')
			elif self._offset + n > self._dataset_size:
				if self._hard_budget and self._drop_last:
					raise self._BudgetExceeded(f'max epochs exceeded: {self._max_samples}')
				elif not self._hard_budget:
					pass # allow the draw to happen and raise in the next draw
				elif not self._drop_last:
					n = self._dataset_size - self._offset
		idx = super().draw(n)
		return idx
	

	def expected_iterations(self, step_size: int) -> Optional[int]:
		num = super().expected_iterations(step_size)
		if num is None and self._max_epochs is not None and self._dataset_size is not None:
			remaining = self._max_epochs * self._dataset_size - self._drawn_samples
			return (remaining // step_size) + (1 if (remaining % step_size > 0 and not (self._hard_budget and self._drop_last)) else 0)
		return num
		

