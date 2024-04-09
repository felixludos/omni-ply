from .imports import *


CHOICE = Union[str, int]


class AbstractDecision(AbstractGaggle):
	@property
	def choice_gizmo(self):
		raise NotImplementedError


	def choices(self, ctx: 'AbstractGame' = None) -> Iterator[CHOICE]:
		raise NotImplementedError



class AbstractCountableDecision(AbstractDecision):
	def count(self, ctx: 'AbstractGame' = None) -> int:
		'''how many choices are available'''
		raise NotImplementedError


	def cover(self, sampling: int, ctx: 'AbstractGame' = None, gizmo: str = None) -> Iterator[int]:
		'''
		sample a "representative" subset of choices from the total set of choices
		(can be uniformly random, if you don't have any better ideas)
		'''
		raise NotImplementedError



class AbstractIndexDecision(AbstractCountableDecision):
	def choices(self, ctx: 'AbstractGame' = None) -> Iterator[str]:
		'''list all choices'''
		yield from range(self.count(ctx))


class AbstractGadgetDecision(AbstractDecision):
	def consequence(self, choice: CHOICE) -> AbstractGadget:
		raise NotImplementedError



class AbstractCase(AbstractGame):
	'''a single iterate'''
	def check(self, decision: AbstractDecision) -> CHOICE:
		raise NotImplementedError



class AbstractChain:
	'''the iterator'''
	@property
	def current(self) -> str:
		raise NotImplementedError


	def confirm(self, case: AbstractCase, decision: AbstractDecision) -> CHOICE:
		raise NotImplementedError


	def __iter__(self):
		return self



class AbstractDecidable:
	def certificate(self) -> Iterator[str]:
		'''returns all the choices made (ie. that are cached)'''
		raise NotImplementedError


	def consider(self, *targets: str) -> Iterator[AbstractGame]:
		raise NotImplementedError


	def create_case(self, cache: dict[str, Any] = None, chain: AbstractChain = None) -> AbstractCase:
		raise NotImplementedError


