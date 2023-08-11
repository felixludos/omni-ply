from .imports import *
from .abstract import *


class AbstractDecision(AbstractTool):
	def choices(self) -> Iterator[Any]:
		raise NotImplementedError


	def grab_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		raise NotImplementedError

	pass



class AbstractContext(AbstractTool):

	def spawn(self, gizmo: str) -> Iterator[Any]:



		raise NotImplementedError





	pass



class ChoiceExpander:
	def __init__(self, fn, choices):
		self.fn = fn
		self.choices = choices
	
	def __iter__(self):
		return self

	def __next__(self):
		parents = {}
		choices = {key: choice for key, choice in parents.items() if isinstance(choice, AbstractDecision)}




		raise NotImplementedError








def test_decisions():



	pass




