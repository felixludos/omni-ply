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



class AbstractEvent(AbstractSetup, AbstractGadget):
	def setup(self, *args, **kwargs) -> None:
		raise NotImplementedError


	def step(self, ctx: AbstractGame) -> None:
		pass


	def end(self, last_ctx: Optional[AbstractGame] = None) -> None:
		pass



class AbstractEngine(AbstractEvent):
	def gadgetry(self) -> Iterator[AbstractGadget]:
		raise NotImplementedError


	def loop(self) -> Iterator[AbstractGame]:
		raise NotImplementedError


	def run(self) -> JSONABLE:
		for _ in self.loop(): pass



class AbstractDataset:
	@property
	def size(self) -> Optional[int]:
		raise NotImplementedError
	
	

class AbstractBatch(AbstractDataset, AbstractGame): # AbstractMogul
	def gadgetry(self) -> Iterator[AbstractGadget]:
		'''all vendors except for the batch specific info'''
		raise NotImplementedError


	def new(self, size: int = None) -> 'AbstractBatch':
		'''fork this batch, optionally with a new size'''
		raise NotImplementedError
	

	@property
	def size(self) -> int:
		'''size of the batch'''
		raise NotImplementedError


	@property
	def plan(self) -> 'AbstractPlanner':
		'''planner for the batch'''
		raise NotImplementedError



class AbstractEvaluator:
	def evaluate_loop(self, src: AbstractDataset) -> Iterator[AbstractBatch]:
		raise NotImplementedError


	def evaluate(self, src: AbstractDataset) -> Any:
		raise NotImplementedError


	def score(self, batch: AbstractBatch) -> AbstractBatch:
		'''single evaluation step'''
		raise NotImplementedError



class AbstractTrainer:
	def gadgetry(self) -> Iterator[AbstractGadget]:
		raise NotImplementedError


	def fit_loop(self, src: AbstractDataset) -> Iterator[AbstractBatch]:
		raise NotImplementedError


	def fit(self, src: AbstractDataset) -> Self:
		raise NotImplementedError


	def learn(self, batch: AbstractBatch) -> AbstractBatch:
		'''single optimization step'''
		raise NotImplementedError


	def environment(self) -> Dict[str, Any]:
		'''prepare the dataset for training'''
		raise NotImplementedError
	
	
	def bearings(self):
		pass



class AbstractPlanner:
	def __init__(self, src: AbstractDataset, **kwargs):
		'''prepare the planner for a new dataset'''
		super().__init__(**kwargs)


	def step(self, size: int) -> Dict[str, Any]:
		'''creates new batch info for an iteration'''
		return self.draw(size)


	def draw(self, size: int) -> Dict[str, Any]:
		'''create the info for a new batch'''
		raise NotImplementedError
	
	
	def generate(self, step_size: int) -> Iterator[Dict[str, Any]]:
		'''generate batch infos with given step size'''
		raise NotImplementedError
	

	def expected_iterations(self, step_size: int) -> Optional[int]:
		'''
		expected number of iterations for given batch size
		None means infinite or unknown
		'''
		raise NotImplementedError

