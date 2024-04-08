from .imports import *


CHOICE = Union[str, int]


class AbstractDecision(AbstractGaggle):
	@property
	def choice_gizmo(self):
		raise NotImplementedError


	def choices(self, ctx: 'AbstractGame' = None, gizmo: str = None) -> Iterator[CHOICE]:
		raise NotImplementedError



class AbstractGadgetDecision(AbstractDecision):
	def consequence(self, choice: CHOICE) -> AbstractGadget:
		raise NotImplementedError



class AbstractCase(AbstractGame):
	'''a single iterate'''
	def check(self, decision: AbstractDecision) -> CHOICE:
		raise NotImplementedError



class AbstractChain:
	'''the iterator'''
	def _create_case(self, prior: dict[str, Any]) -> AbstractGame:
		raise NotImplementedError


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



