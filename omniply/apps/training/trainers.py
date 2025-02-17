from .imports import *

from .abstract import AbstractTrainer, AbstractDataset, AbstractBatch, AbstractPlanner
from .planners import Indexed, BudgetExceeded
from .batches import Batch
from .datasets import Dataset



class TrainerBase(ToolKit, AbstractTrainer):
	def __init__(self, *, batch_size: int = None, **kwargs):
		super().__init__(**kwargs)
		self._batch_size = batch_size


	def gadgetry(self) -> Iterator[AbstractGadget]:
		'''gadgets to include in the batch'''
		yield from ()


	def _terminate_fit(self, batch: Batch) -> bool:
		'''is the training done?'''
		return False
	

	_Planner = Indexed
	_Batch = None #Batch
	def fit_loop(self, src: Dataset, **settings: Any) -> Iterator[Batch]:
		'''train the model'''
		planner = self._Planner(src, **settings)

		batch_size = 32 if self._batch_size is None else self._batch_size

		num_itr = planner.expected_iterations(batch_size) # to get the total number of iterations

		batch_cls = self._Batch or getattr(src, '_Batch', None) or Batch
		for info in planner.generate(batch_size):
			batch = batch_cls(info, planner=planner).include(src, self)

			# Note: this runs the optimization step before yielding the batch
			yield self.learn(batch)

			if self._terminate_fit(batch):
				break


	def fit(self, src: Dataset) -> Self:
		'''train the model'''
		for batch in self.fit_loop(src): pass
		return self

	
	def learn(self, batch: Batch) -> Batch:
		'''single optimization step'''
		raise NotImplementedError



# class DynamicTrainerBase(TrainerBase):
# 	def __init__(self, **kwargs):
# 		super().__init__(**kwargs)
# 		self._gadgetry = []
#
#
# 	def include(self, *gadgets: AbstractGadget) -> Self:
# 		'''include gadgets in the batch'''
# 		self._gadgetry.extend(gadgets)
# 		return self
#
#
# 	def extend(self, gadgets: Iterable[AbstractGadget]) -> Self:
# 		'''extend the batch with gadgets'''
# 		self._gadgetry.extend(gadgets)
# 		return self
#
#
# 	def exclude(self, *gadgets: AbstractGadget) -> Self:
# 		'''exclude gadgets from the batch'''
# 		for gadget in gadgets:
# 			self._gadgetry.remove(gadget)
# 		return self
#
#
# 	def gadgetry(self) -> Iterator[ToolKit]:
# 		'''gadgets to include in the batch'''
# 		yield from self._gadgetry


