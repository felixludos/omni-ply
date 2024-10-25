from .imports import *

from .abstract import AbstractTrainer, AbstractDataset, AbstractBatch, AbstractPlanner
from .planners import Indexed, BudgetExceeded
from .batches import Batch
from .datasets import Dataset



class TrainerBase(AbstractTrainer):
	def __init__(self, *, planner: AbstractPlanner = None, batch_size: int = None, **kwargs):
		if planner is None:
			planner = self._Planner()
		super().__init__(**kwargs)
		self._planner = planner
		self._batch_size = batch_size


	def gadgetry(self) -> Iterator[AbstractGadget]:
		'''gadgets to include in the batch'''
		yield self._planner


	def fit_is_done(self, batch: Batch) -> bool:
		'''is the training done?'''
		return False
	

	_Planner = Indexed
	_Batch = Batch
	def fit_loop(self, src: Dataset, **settings: Any) -> Iterator[Batch]:
		'''train the model'''
		self._planner.setup(src, **settings) # TODO: convert this to be a context manager

		batch_size = 32 if self._batch_size is None else self._batch_size

		try:
			while True:
				batch = self._Batch(self._planner.step(batch_size), planner=self._planner)
				batch.include(src).extend(list(self.gadgetry()))

				yield self.learn(batch)
				
				if self.fit_is_done(batch):
					break
		except BudgetExceeded:
			pass

	
	def learn(self, batch: Batch) -> Batch:
		'''single optimization step'''
		raise NotImplementedError



class DynamicTrainerBase(TrainerBase):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._gadgetry = []


	def include(self, *gadgets: AbstractGadget) -> Self:
		'''include gadgets in the batch'''
		self._gadgetry.extend(gadgets)
		return self


	def extend(self, gadgets: Iterable[AbstractGadget]) -> Self:
		'''extend the batch with gadgets'''
		self._gadgetry.extend(gadgets)
		return self


	def exclude(self, *gadgets: AbstractGadget) -> Self:
		'''exclude gadgets from the batch'''
		for gadget in gadgets:
			self._gadgetry.remove(gadget)
		return self


	def gadgetry(self) -> Iterator[AbstractGadget]:
		'''gadgets to include in the batch'''
		yield from super().gadgetry()
		yield from self._gadgetry



