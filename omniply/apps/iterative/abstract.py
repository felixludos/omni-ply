from .imports import *



class AbstractGuru:
	def gadgetry(self) -> Iterator[AbstractGadget]:
		raise NotImplementedError



class AbstractGod:
	'''source that can generate a stream of contexts given a base (mogul)'''
	def grant(self, base: AbstractGuru | Iterable[AbstractGadget] = None) -> Iterator[AbstractGame]:
		raise NotImplementedError



class AbstractEvaluator(AbstractGuru):
	def evaluate(self, src: AbstractGod) -> Any:
		for ctx in src.grant(self):
			yield self.eval_step(ctx)


	def eval_step(self, ctx: AbstractGame) -> AbstractGame:
		raise NotImplementedError



class AbstractTrainer(AbstractEvaluator):
	def fit(self, src: AbstractGod) -> Any:
		for ctx in src.grant(self):
			yield self.learn(ctx)


	def learn(self, ctx: AbstractGame) -> AbstractGame:
		'''single optimization step'''
		raise NotImplementedError



class AbstractGenie(AbstractGuru, AbstractGod):
	def grant(self, base: 'AbstractGenius' = None) -> Iterator[AbstractGame]:
		'''emits games from goals'''
		if isinstance(base, AbstractGenius):
			for goal in base.grant(base):
				raise NotImplementedError
		return super().grant(base)



class AbstractGenius(AbstractGenie):
	def grant(self, base: AbstractGod = None) -> Iterator[AbstractGame]:
		'''emits goals for a genie to transform into games'''
		raise NotImplementedError





class GeniusBase(AbstractGenius):
	_Goal = None


	def grant(self, base: AbstractGuru | Iterator[AbstractGadget] = None) -> Iterator[AbstractGame]:
		goal = self._Goal(base)
		for progress in sprint:
			yield progress
			if progress.grab('stop', False):
				break



