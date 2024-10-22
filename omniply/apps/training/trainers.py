from .imports import *

from .abstract import AbstractTrainer, AbstractDataset, AbstractBatch, AbstractPlanner
from .planners import Indexed, BudgetExceeded
from .batches import Batch
from .datasets import Dataset



class TrainerBase(AbstractTrainer):
	def __init__(self, model, *, planner: AbstractPlanner = None, batch_size: int = None, **kwargs):
		if planner is None:
			planner = self._Planner()
		super().__init__(**kwargs)
		self._model = model
		self._planner = planner
		self._batch_size = batch_size
		

	def gadgetry(self) -> Iterator[AbstractGadget]:
		'''gadgets to include in the batch'''
		yield self._model
		yield self._planner


	def fit_is_done(self, batch: Batch) -> bool:
		'''is the training done?'''
		return False
	

	_Planner = Indexed
	_Batch = Batch
	def fit_loop(self, src: Dataset) -> Iterator[Batch]:
		'''train the model'''
		self._planner.setup(src)

		batch_size = src.suggest_batch_size() if self._batch_size is None else self._batch_size

		try:
			while True:
				batch = self._Batch(self._planner.step(batch_size), planner=self._planner)
				batch.include(src).extend(self.gadgetry())

				yield self.learn(batch)
				
				if self.fit_is_done(batch):
					break
		except BudgetExceeded:
			pass

	
	def learn(self, batch: Batch) -> Batch:
		'''single optimization step'''
		raise NotImplementedError






