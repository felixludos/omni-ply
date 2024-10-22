from .imports import *

from .abstract import AbstractTrainer, AbstractDataset, AbstractGoal, AbstractBudget
from .goals import Sized, Indexed, Goal, BudgetExceeded





class TrainerBase(AbstractTrainer):
	def __init__(self, *, model, optimizer, planner: AbstractBudget, objective: str = 'loss', **kwargs):
		super().__init__(**kwargs)
		self._planner = planner
		self._model = model
		self._optimizer = optimizer
		self._objective = objective


	def gadgetry(self) -> Iterator[AbstractGadget]:
		'''gadgets to include in the batch'''
		yield self._model
		yield self._optimizer


	_Goal = Context
	_Planner = Indexed
	def _create_goal(self, src: AbstractDataset) -> AbstractGoal:
		return self._Goal(self._budget)
	

	_Batch = Batch
	def _create_batch(self, src: AbstractDataset, goal: AbstractGoal) -> AbstractGame:
		return self._Batch(goal).extend(self.gadgetry()).include(src)


	def fit_is_done(self, batch: AbstractGoal) -> bool:
		'''is the training done?'''
		return self._budget.is_complete()
	

	def fit_loop(self, src: AbstractDataset) -> Iterator[AbstractGame]:
		'''train the model'''
		self._planner.setup(src)
		self._optimizer.setup(self._model)

		goal = self._create_goal(src)
		batch = self._create_batch(src, goal)
		try:
			while not self.fit_is_done(batch):
				batch = batch.new()
				yield self.learn(batch)
		except BudgetExceeded:
			pass

	
	def learn(self, batch: AbstractGame) -> AbstractGame:
		'''single optimization step'''
		self._optimizer.step(batch)






