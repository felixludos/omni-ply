from typing import Union, Any, Iterator, Type, Self, Optional
from .imports import *


class AbstractBatch(AbstractGame):
	def new(self, size: int = None) -> 'AbstractBatch':
		'''create a copy of this batch with a new size'''
		raise NotImplementedError
	
	@property	
	def size(self) -> int:
		'''size of the batch'''
		raise NotImplementedError



class AbstractGoal(AbstractBatch):
	'''a meta batch'''
	def new(self, size: int = None) -> 'AbstractGoal':
		'''create a copy of this goal with a new size'''
		raise NotImplementedError


	def is_achieved(self):
		'''is the goal achieved?'''
		raise NotImplementedError



class AbstractGod:
	'''generates goals'''
	def grant(self, cond: Optional[Any] = None, /, **settings: Any) -> Iterator[AbstractGame]:
		'''generates goals'''
		raise NotImplementedError
	


class AbstractDriver:
	def gadgetry(self) -> Iterator[AbstractGadget]:
		'''gadgets that should be included in the game'''
		raise NotImplementedError



class AbstractMogul:
	def iterate(self, cond: Optional[Any] = None, /, **settings: Any) -> Iterator[AbstractGame]:
		raise NotImplementedError
	

	def __iter__(self):
		return self.iterate()
	

	def __next__(self):
		return next(self.iterate())



class AbstractGuru(AbstractMogul):
	'''can use goals to create games'''
	def iterate(self, cond: Union[AbstractGod, None] = None, /, **settings: Any) -> Iterator[AbstractGame]:
		if isinstance(cond, AbstractGod):
			for goal in cond.grant(self):
				yield self.glean(goal)
		raise NotImplementedError
	

	def glean(self, goal: AbstractGame) -> AbstractGame:
		'''create a game using the meta (goal)'''
		raise NotImplementedError



class AbstractEvaluator(AbstractGod):
	def evaluate_loop(self, src: AbstractMogul) -> Iterator[AbstractGame]:
		for ctx in src.iterate(self):
			yield self.score(ctx)


	def evaluate(self, src: AbstractMogul) -> Any:
		raise NotImplementedError


	def score(self, ctx: AbstractGame) -> AbstractGame:
		'''single evaluation step'''
		raise NotImplementedError



class AbstractTrainer(AbstractGod):
	def fit_loop(self, src: AbstractMogul) -> Iterator[AbstractGame]:
		for ctx in src.iterate(self):
			yield self.learn(ctx)


	def fit(self, src: AbstractMogul) -> Self:
		raise NotImplementedError


	def learn(self, ctx: AbstractGame) -> AbstractGame:
		'''single optimization step'''
		raise NotImplementedError



class AbstractDataset(AbstractGuru):
	@property
	def size(self) -> int:
		raise NotImplementedError
	

	def __len__(self) -> int:
		return self.size


class AbstractBudget:
	

