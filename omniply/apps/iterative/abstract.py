from .imports import *



class AbstractMogul(AbstractGaggle):
	def gadgetry(self) -> Iterator[AbstractGadget]:
		raise NotImplementedError


	# def announce(self, src: 'AbstractInnovator') -> Iterator[AbstractGig]:
	# 	for ctx in src.innovate(self):
	# 		yield self.step(ctx)
	#
	#
	# def step(self, ctx: AbstractGig) -> AbstractGig:
	# 	raise NotImplementedError



class AbstractGuru:
	'''source that can generate a stream of contexts given a base (mogul)'''
	def guide(self, base: AbstractMogul | Iterable[AbstractGadget] = None) -> Iterator[AbstractGig]:
		raise NotImplementedError



class AbstractEvaluator(AbstractMogul):
	def evaluate(self, guru: AbstractGuru) -> Any:
		for ctx in guru.guide(self):
			yield self.eval_step(ctx)


	def eval_step(self, ctx: AbstractGig) -> AbstractGig:
		raise NotImplementedError



class AbstractTrainer(AbstractEvaluator):
	def fit(self, src: AbstractGuru) -> Any:
		for ctx in src.guide(self):
			yield self.learn(ctx)


	def learn(self, ctx: AbstractGig) -> AbstractGig:
		'''single optimization step'''
		raise NotImplementedError



class AbstractProgressiveMogul(AbstractMogul, AbstractGuru):
	_Sprint = None

	def guide(self, base: AbstractMogul | Iterator[AbstractGadget] = None) -> Iterator[AbstractGig]:
		sprint = self._Sprint(base)
		for progress in sprint:
			yield progress
			if progress.grab('stop', False):
				break



