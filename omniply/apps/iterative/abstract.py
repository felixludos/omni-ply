from .imports import *



class AbstractGuru:
	def gadgetry(self) -> Iterator[AbstractGadget]:
		raise NotImplementedError



class AbstractGod:
	'''source that can generate a stream of contexts given a base (mogul)'''
	def grant(self, base: AbstractGuru | Iterable[AbstractGadget] = None) -> Iterator[AbstractGig]:
		raise NotImplementedError



class AbstractEvaluator(AbstractGuru):
	def evaluate(self, src: AbstractGod) -> Any:
		for ctx in src.grant(self):
			yield self.eval_step(ctx)


	def eval_step(self, ctx: AbstractGig) -> AbstractGig:
		raise NotImplementedError



class AbstractTrainer(AbstractEvaluator):
	def fit(self, src: AbstractGod) -> Any:
		for ctx in src.grant(self):
			yield self.learn(ctx)


	def learn(self, ctx: AbstractGig) -> AbstractGig:
		'''single optimization step'''
		raise NotImplementedError



class AbstractGenie(AbstractGuru, AbstractGod):
	def grant(self, base: 'AbstractGenius' = None) -> Iterator[AbstractGig]:
		'''emits gigs from goals'''
		if isinstance(base, AbstractGenius):
			for goal in base.grant(base):
				raise NotImplementedError
		return super().grant(base)



class AbstractGenius(AbstractGenie):
	def grant(self, base: AbstractGod = None) -> Iterator[AbstractGig]:
		'''emits goals for a genie to transform into gigs'''
		raise NotImplementedError





class GeniusBase(AbstractGenius):
	_Goal = None


	def grant(self, base: AbstractGuru | Iterator[AbstractGadget] = None) -> Iterator[AbstractGig]:
		goal = self._Goal(base)
		for progress in sprint:
			yield progress
			if progress.grab('stop', False):
				break



