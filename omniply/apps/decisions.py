from typing import Iterator, Any, Iterable, Mapping
import random
from omnibelt import filter_duplicates

from ..core.abstract import AbstractGadget, AbstractGaggle, AbstractGig
from ..core.gadgets import SingleGadgetBase
from ..core.gaggles import GaggleBase




class AbstractDecision(AbstractGaggle):
	def gizmos(self) -> Iterator[str]:
		yield self.choice_gizmo
		yield from super().gizmos()


	@property
	def choice_gizmo(self):
		raise NotImplementedError


	def choices(self, gizmo: str = None) -> Iterator[str]:
		raise NotImplementedError


	def consider(self, choice: str | int) -> AbstractGadget:
		raise NotImplementedError



class NoOptionsError(Exception):
	pass



class DecisionBase(AbstractDecision):
	def __init__(self, choices: Iterable[AbstractGadget] | Mapping[str, AbstractGadget] = None, *,
				 choice_gizmo: str = None, **kwargs):
		if choices is None:
			choices = {}
		if not isinstance(choices, Mapping):
			choices = {str(i): choice for i, choice in enumerate(choices)}
		super().__init__(**kwargs)
		self._choices = dict(choices)
		self._option_table = {}
		self._choice_gizmo = choice_gizmo
		for choice, option in self._choices.items():
			for gizmo in option.gizmos():
				self._option_table.setdefault(gizmo, []).append(choice)

	@property
	def choice_gizmo(self):
		return self._choice_gizmo


	def choices(self, gizmo: str = None) -> Iterator[str]:
		yield from self._choices.keys() if gizmo is None else self._option_table.get(gizmo, ())


	def _commit(self, ctx: 'AbstractGig', choice: str, gizmo: str) -> Any:
		'''after a choice has been selected, this method is called to determine the final result.'''
		return self._choices[choice].grab_from(ctx, gizmo)


	_NoOptionsError = NoOptionsError
	def _choose(self, ctx: 'AbstractGig') -> str:
		'''this method is called to determine the choice to be made.'''
		rng = getattr(ctx, 'rng', random)
		options = list(self.choices())
		if len(options) == 0:
			raise self._NoOptionsError(f'No options available for decision: {self}')
		return rng.choice(options)


	def grab_from(self, ctx: 'AbstractGig', gizmo: str) -> Any:
		if gizmo == self.choice_gizmo:
			return self._choose(ctx)
		choice = ctx.grab(self.choice_gizmo)
		return self._commit(ctx, choice, gizmo)



class DynamicDecision(DecisionBase):
	def add_choice(self, option: AbstractGadget, choice: str = None):
		if choice is None:
			choice = str(len(self._choices))
		assert choice not in self._choices, f'Choice {choice!r} already exists, specify a different choice name.'
		self._choices[choice] = option
		for gizmo in option.gizmos():
			self._option_table.setdefault(gizmo, []).append(choice)



class SelfSelectingDecision(DecisionBase):
	def __init__(self, choices: Iterable[AbstractGadget] | Mapping[str, AbstractGadget] = None, *,
				 choice_gizmo: str = None, **kwargs):
		super().__init__(choices, choice_gizmo=choice_gizmo, **kwargs)
		self._waiting_gizmo = None


	_NoOptionsError = NoOptionsError
	def _choose(self, ctx: 'AbstractGig') -> str:
		'''this method is called to determine the choice to be made.'''
		rng = getattr(ctx, 'rng', random)
		options = list(self.choices() if self._waiting_gizmo is None else self.choices(self._waiting_gizmo))
		if len(options) == 0:
			raise self._NoOptionsError(f'No options available for decision: {self}')
		return rng.choice(options)


	def grab_from(self, ctx: 'AbstractGig', gizmo: str) -> Any:
		prev = self._waiting_gizmo
		if gizmo != self.choice_gizmo:
			self._waiting_gizmo = gizmo
		out = super().grab_from(ctx, gizmo)
		self._waiting_gizmo = prev
		return out



from ..core.genetics import AbstractGenetic




class AbstractDecidable(AbstractGig):
	def condition(self, target: str, prior: dict[str, Any]) -> Iterator[AbstractGig]:
		raise NotImplementedError




class NaiveDecidable(GaggleBase, AbstractDecidable):
	def condition(self, target: str, *, given: dict[str, Any] = None) -> Iterator[AbstractGig]:
		given = given or {}

		todo = [target]

		loops = {}

		while len(todo):
			gizmo = todo.pop()
			for candidate in loops.setdefault(gizmo, self.gadgets(gizmo)):
				if isinstance(candidate, AbstractDecision):
					if candidate.choice_gizmo in given:
						operator = candidate.consider(given[candidate.choice_gizmo])
					else:
						for option in candidate.choices(target):
							given[candidate.choice_gizmo] = option
							yield from self.condition(option, given=given) # expand this decision
						break

				else:
					operator = candidate

				if not isinstance(operator, AbstractGenetic):
					raise NotImplementedError(f'{operator} has unknown genetics')

				gene = next(operator.genes(gizmo))
				for parent in gene.parents:
					if parent not in given:
						todo.append(parent)


		# create context with the given prior

		


		pass








