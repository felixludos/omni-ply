from .imports import *



# class AbstractDriver:
# 	def gadgetry(self) -> Iterator[AbstractGadget]:
# 		'''gadgets that should be included in the game'''
# 		raise NotImplementedError



# class AbstractMogul:
# 	def iterate(self, cond: Optional[Any] = None, /, **settings: Any) -> Iterator[AbstractGame]:
# 		raise NotImplementedError
	

# 	def __iter__(self):
# 		return self.iterate()
	

# 	def __next__(self):
# 		return next(self.iterate())



# class AbstractGuru(AbstractMogul):
# 	'''can use goals to create games'''
# 	def iterate(self, cond: Union[AbstractGod, None] = None, /, **settings: Any) -> Iterator[AbstractGame]:
# 		if isinstance(cond, AbstractGod):
# 			for goal in cond.grant(self):
# 				yield self.glean(goal)
# 		raise NotImplementedError
	

# 	def glean(self, goal: AbstractGame) -> AbstractGame:
# 		'''create a game using the meta (goal)'''
# 		raise NotImplementedError



class AbstractDataset:
	@property
	def size(self) -> Optional[int]:
		raise NotImplementedError
	

	# def __len__(self) -> int:
	# 	return self.size



class AbstractBatch(AbstractDataset, AbstractGame): # AbstractMogul
	def new(self, size: int = None) -> 'AbstractBatch':
		'''fork this batch, optionally with a new size'''
		raise NotImplementedError
	

	@property	
	def size(self) -> int:
		'''size of the batch'''
		raise NotImplementedError



class AbstractEvaluator:
	def evaluate_loop(self, src: AbstractDataset) -> Iterator[AbstractBatch]:
		for ctx in src.iterate(self):
			yield self.score(ctx)


	def evaluate(self, src: AbstractDataset) -> Any:
		raise NotImplementedError


	def score(self, batch: AbstractBatch) -> AbstractBatch:
		'''single evaluation step'''
		raise NotImplementedError



class AbstractTrainer:
	def fit_loop(self, src: AbstractDataset) -> Iterator[AbstractBatch]:
		for ctx in src.iterate(self):
			yield self.learn(ctx)


	def fit(self, src: AbstractDataset) -> Self:
		raise NotImplementedError


	def learn(self, batch: AbstractBatch) -> AbstractBatch:
		'''single optimization step'''
		raise NotImplementedError



class AbstractPlanner:
	def setup(self, src: AbstractDataset) -> Optional[int]:
		'''prepare the planner for a new dataset'''
		raise NotImplementedError


	def step(self, size: int) -> dict[str, Any]:
		'''creates a new batch for an iteration'''
		return self.draw(size)


	def draw(self, size: int) -> dict[str, Any]:
		'''create the info for a new batch'''
		raise NotImplementedError
	
