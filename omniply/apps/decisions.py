from typing import Iterator, Any, Iterable, Mapping, Self, Union, Callable
import random
from omnibelt import filter_duplicates

from ..core.abstract import AbstractGadget, AbstractGaggle, AbstractGame
from ..core.gadgets import SingleGadgetBase
from ..core.genetics import AbstractGenetic, GeneticBase
from ..core.gaggles import GaggleBase, MultiGadgetBase



class AbstractDecision(AbstractGaggle):
	@property
	def choice_gizmo(self):
		raise NotImplementedError


	def choices(self, gizmo: str = None) -> Iterator[str]:
		raise NotImplementedError



class AbstractDynamicDecision(AbstractDecision):
	def add_choice(self, option: AbstractGadget, choice: str = None) -> Self:
		raise NotImplementedError



class AbstractGadgetDecision(AbstractDecision):
	def consequence(self, choice: str | int) -> AbstractGadget:
		raise NotImplementedError



class AbstractDecidable:
	def certificate(self) -> Iterator[str]:
		'''returns all the choices made (ie. that are cached)'''
		raise NotImplementedError


	def consider(self, target: str, prior: dict[str, Any]) -> Iterator[AbstractGame]:
		raise NotImplementedError



class NoOptionsError(Exception):
	pass


CHOICE = Union[str, int]


class DecisionBase(MultiGadgetBase, AbstractDecision):
	def __init__(self, *, choice_gizmo: str, **kwargs):
		super().__init__(**kwargs)
		self._choice_gizmo = choice_gizmo


	def gizmos(self) -> Iterator[str]:
		yield from super().gizmos()
		yield self.choice_gizmo


	@property
	def choice_gizmo(self):
		return self._choice_gizmo


	_NoOptionsError = NoOptionsError
	def _choose(self, ctx: 'AbstractGame') -> str:
		'''this method is called to determine the choice to be made.'''
		rng = getattr(ctx, 'rng', random)
		options = list(self.choices())
		if len(options) == 0:
			raise self._NoOptionsError(f'No options available for decision: {self}')
		return rng.choice(options)


	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
		if gizmo == self.choice_gizmo:
			return self._choose(ctx)
		choice = ctx.grab(self.choice_gizmo)
		return self._commit(ctx, choice, gizmo)


	def _commit(self, ctx: 'AbstractGame', choice: CHOICE, gizmo: str) -> Any:
		'''after a choice has been selected, this method is called to determine the final result.'''
		raise NotImplementedError



class SimpleDecision(DecisionBase, SingleGadgetBase, GeneticBase, AbstractDynamicDecision):
	def __init__(self, gizmo: str, choices: Iterable[Any] | Mapping[str, Any] = None, *,
				 choice_gizmo: str = None, **kwargs):
		if choice_gizmo is None:
			choice_gizmo = f'{gizmo}_choice'
		if choices is None:
			choices = {}
		if not isinstance(choices, Mapping):
			choices = {i: choice for i, choice in enumerate(choices)}
		super().__init__(gizmo=gizmo, choice_gizmo=choice_gizmo, **kwargs)
		self._choices = dict(choices)


	def _genetic_information(self, gizmo: str):
		return {**super()._genetic_information(gizmo), 'parents': ()}


	def choices(self, gizmo: str = None) -> Iterator[str]:
		yield from self._choices.keys()


	def add_choice(self, option: Any, choice: CHOICE = None) -> Self:
		if choice is None:
			choice = len(self._choices)
		assert choice not in self._choices, f'Choice {choice!r} already exists, specify unique choice name.'
		self._choices[choice] = option
		return self


	def _commit(self, ctx: 'AbstractGame', choice: CHOICE, gizmo: str) -> Any:
		'''after a choice has been selected, this method is called to determine the final result.'''
		return self._choices[choice]



class GadgetDecisionBase(DecisionBase, AbstractGadgetDecision):
	def __init__(self, choices: Iterable[AbstractGadget] | Mapping[str, AbstractGadget] = None, **kwargs):
		if choices is None:
			choices = {}
		if not isinstance(choices, Mapping):
			choices = {i: choice for i, choice in enumerate(choices)}
		super().__init__(**kwargs)
		self._choices = dict(choices)
		self._option_table = {}
		for choice, option in self._choices.items():
			for gizmo in option.gizmos():
				self._option_table.setdefault(gizmo, []).append(choice)


	def gizmos(self) -> Iterator[str]:
		yield from filter_duplicates(*(self.consequence(choice).gizmos() for choice in self.choices()))
		yield self.choice_gizmo


	def _commit(self, ctx: 'AbstractGame', choice: CHOICE, gizmo: str) -> Any:
		'''after a choice has been selected, this method is called to determine the final result.'''
		return self._choices[choice].grab_from(ctx, gizmo)


	def consequence(self, choice: CHOICE) -> AbstractGadget:
		return self._choices[choice]


	def choices(self, gizmo: str = None) -> Iterator[str]:
		yield from self._choices.keys() if gizmo is None else self._option_table.get(gizmo, ())



class DynamicDecision(GadgetDecisionBase):
	def add_choice(self, option: AbstractGadget, choice: CHOICE = None):
		if choice is None:
			choice = str(len(self._choices))
		assert choice not in self._choices, f'Choice {choice!r} already exists, specify unique choice name.'
		self._choices[choice] = option
		for gizmo in option.gizmos():
			self._option_table.setdefault(gizmo, []).append(choice)



class SelfSelectingDecision(GadgetDecisionBase):
	_waiting_gizmo = None


	def _choose(self, ctx: 'AbstractGame') -> str:
		'''this method is called to determine the choice to be made.'''
		rng = getattr(ctx, 'rng', random)
		options = list(self.choices() if self._waiting_gizmo is None else self.choices(self._waiting_gizmo))
		if len(options) == 0:
			raise self._NoOptionsError(f'No options available for decision: {self}')
		return rng.choice(options)


	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
		prev = self._waiting_gizmo
		if gizmo != self.choice_gizmo:
			self._waiting_gizmo = gizmo
		out = super().grab_from(ctx, gizmo)
		if gizmo != self.choice_gizmo:
			self._waiting_gizmo = prev
		return out



class NaiveConsiderationBase(AbstractDecidable):
	def _create_case(self, cache: dict[str, Any]) -> AbstractGame:
		raise NotImplementedError


	def _consider(self, *, targets: Iterable[str], cache: dict[str, Any],
				  get_gadgets: Callable[[str], Iterator[AbstractGadget]],
				  resolved: set[str]) -> Iterator[AbstractGame]:
		todo = list(targets)
		for gizmo in todo:
		# while len(todo):
			# gizmo = todo.pop() # targets
			if gizmo in resolved: # already resolved or cached
				continue

			for gadget in get_gadgets(gizmo):
				while isinstance(gadget, AbstractGadgetDecision) and gadget.choice_gizmo in cache:
					# decision has already been made, follow the consequence
					gadget = gadget.consequence(cache[gadget.choice_gizmo])
				else:
					if isinstance(gadget, AbstractDecision):
						if gadget.choice_gizmo in cache:
							break
						# iterate through choices and then check this gizmo as resolved
						choices = list(gadget.choices(gizmo)) # technically optional to check that choices exist
						assert len(choices), f'No choices available for decision to produce {gizmo}'
						# resolved.add(gizmo) # prevent this decision from getting expanded again
						for choice in choices:
							cache[gadget.choice_gizmo] = choice
							yield from self._consider(targets=todo, resolved=resolved.copy(), get_gadgets=get_gadgets, cache=cache.copy())
						return # skip base case yield

				# expand gadget to find required parents and continue search (while)
				assert isinstance(gadget, AbstractGenetic), f'{gadget} has unknown genetics'

				gene = next(gadget.genes(gizmo))
				if gizmo in gene.parents:
					raise NotImplementedError(f'Loopy case not supported yet')
				todo.extend(parent for parent in gene.parents if parent not in resolved)
				break
			else:
				raise NotImplementedError(f'No gadget found to produce {gizmo}')

		# create context with the given prior
		yield self._create_case(cache)



from ..core import Context

from .simple import DictGadget



class GadgetDecision(DynamicDecision, SelfSelectingDecision, GadgetDecisionBase):
	pass



class Controller(Context, NaiveConsiderationBase):
	def certificate(self) -> dict[str, CHOICE]:
		return {gizmo: self[gizmo] for gizmo in self.cached()
				if isinstance(decision := next(self._gadgets(gizmo)), AbstractDecision)
				and gizmo == decision.choice_gizmo}


	def _create_case(self, cache: dict[str, Any]) -> AbstractGame:
		case = self.gabel()
		case.data.update(cache)
		# case.include(DictGadget(cache.copy()))
		return case

	def consider(self, *targets: str) -> Iterator[AbstractGame]:
		given = {gizmo: self[gizmo] for gizmo in self.cached()}
		yield from self._consider(targets=targets, resolved=set(given.keys()), cache=dict(given),
								  get_gadgets=self._vendors)







