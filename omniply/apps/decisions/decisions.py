from .imports import *

from .abstract import (AbstractDecision, AbstractIndexDecision, AbstractGadgetDecision, CHOICE,
					   AbstractCountableDecision)
from .errors import NoOptionsError




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
		options = list(self.choices(ctx))
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


# TODO: enable setting a weight to each of the choices!
# class WeightedDecision(DecisionBase):
# 	pass




class CountableDecisionBase(DecisionBase, AbstractCountableDecision):
	def cover(self, sampling: int, ctx: 'AbstractGame' = None, gizmo: str = None) -> Iterator[int]:
		for _ in range(sampling):
			yield self._choose(ctx)



class LargeDecision(CountableDecisionBase, AbstractIndexDecision):
	'''
	expects choices to always be integers from [0, self.count())
	'''
	def _choose(self, ctx: 'AbstractGame') -> int:
		'''this method is called to determine the choice to be made.'''
		rng = getattr(ctx, 'rng', random)
		N = self.count(ctx)
		assert N > 0, f'No options available for decision: {self}'
		return rng.randint(0, N - 1)




class SimpleDecisionBase(DecisionBase, SingleGadgetBase, GeneticBase):
	def __init__(self, gizmo: str, choice_gizmo: str = None, **kwargs):
		if choice_gizmo is None:
			choice_gizmo = f'{gizmo}_choice'
		assert choice_gizmo is not None, f'Choice gizmo must be specified for decision: {gizmo}'
		super().__init__(gizmo=gizmo, choice_gizmo=choice_gizmo, **kwargs)


	def _genetic_information(self, gizmo: str):
		return {**super()._genetic_information(gizmo), 'parents': ()}



class GadgetDecisionBase(DecisionBase, AbstractGadgetDecision):
	def __init__(self, choices: Iterable[AbstractGadget] | Mapping[str, AbstractGadget] = None, **kwargs):
		if choices is None:
			choices = {}
		if not isinstance(choices, Mapping):
			choices = {i: choice for i, choice in enumerate(choices)}
		super().__init__(**kwargs)
		self._choices = dict(choices)


	def gizmos(self) -> Iterator[str]:
		yield from filter_duplicates(*(self.consequence(choice).gizmos() for choice in self.choices()))
		yield self.choice_gizmo


	def _commit(self, ctx: 'AbstractGame', choice: CHOICE, gizmo: str) -> Any:
		'''after a choice has been selected, this method is called to determine the final result.'''
		return self._choices[choice].grab_from(ctx, gizmo)


	def consequence(self, choice: CHOICE) -> AbstractGadget:
		return self._choices[choice]


	def choices(self, ctx: 'AbstractGame' = None) -> Iterator[str]:
		yield from self._choices.keys()



class SelfSelectingDecision(GadgetDecisionBase):
	def __init__(self, choices: Iterable[AbstractGadget] | Mapping[str, AbstractGadget] = None, **kwargs):
		super().__init__(choices=choices, **kwargs)
		self._waiting_gizmo = None
		self._option_table = {}
		for choice, option in self._choices.items():
			for gizmo in option.gizmos():
				self._option_table.setdefault(gizmo, []).append(choice)


	def choices(self, ctx: 'AbstractGame' = None) -> Iterator[str]:
		yield from super().choices(ctx) if self._waiting_gizmo is None \
			else self._option_table.get(self._waiting_gizmo, ())


	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
		prev = self._waiting_gizmo
		if gizmo != self.choice_gizmo:
			self._waiting_gizmo = gizmo
		out = super().grab_from(ctx, gizmo)
		if gizmo != self.choice_gizmo:
			self._waiting_gizmo = prev
		return out



class DynamicDecision(SelfSelectingDecision):
	def add_choice(self, option: AbstractGadget, choice: CHOICE = None):
		if choice is None:
			choice = str(len(self._choices))
		assert choice not in self._choices, f'Choice {choice!r} already exists, specify unique choice name.'
		self._choices[choice] = option
		for gizmo in option.gizmos():
			self._option_table.setdefault(gizmo, []).append(choice)





# class Enumeration(AutoDecision, ToolKit): # sketch
# 	def __init__(self, element_gizmos: list[str], **kwargs):
# 		super().__init__(**kwargs)
# 		self.include(Permutation(N=len(element_gizmos), gizmo='order'))
# 		self._aggregator = 'and'
#
#
# 	@choice
# 	def single_element(self, elements):
# 		return elements if len(elements) else ''
# 	@single_element.condition
# 	def _check_single_element(self, elements):
# 		return len(elements) <= 1
#
# 	@choice
# 	def multi_element(self, elements, order, aggregator=None):
# 		if aggregator is None:
# 			aggregator = self._aggregator
# 		fixed = [elements[idx] for idx in order]
# 		return f'{", ".join(fixed[:-1])} {aggregator} {fixed[-1]}'
# 	@multi_element.condition
# 	def _check_multi_element(self, elements):
# 		return len(elements) > 1


# TODO for combinations:
#   sampling: https://cs.stackexchange.com/questions/104930/efficient-n-choose-k-random-sampling
#   generation: https://math.stackexchange.com/questions/1227409/indexing-all-combinations-without-making-list


# class CommonPool(ToolKit):
# 	def __init__(self, population: int, pool: Iterable[Any], **kwargs):
# 		pool = tuple(pool)
# 		assert len(pool) >= population, f'Not enough elements in pool: {len(pool)} < {population}'
# 		super().__init__(**kwargs)
# 		self.include(Permutation(population, gizmo='order'))
# 		self._pool = pool
#
# 	pass


# adapted from https://math.stackexchange.com/questions/1227409/indexing-all-combinations-without-making-list
# def C(n,k): #computes nCk, the number of combinations n choose k
#     result = 1
#     for i in range(n):
#         result*=(i+1)
#     for i in range(k):
#         result//=(i+1)
#     for i in range(n-k):
#         result//=(i+1)
#     return result
#
# def cgen(i,n,k):
#     """
#     returns the i-th combination of k numbers chosen from 0,1,2,...,n-1
#     """
#     mx = C(n,k)
#     assert 0 <= i <= mx, f"i must be in [0, {mx}]"
#     c = []
#     r = i+0
#     j = 0
#     for s in range(1,k+1):
#         cs = j+1
#         while r-C(n-cs,k-s)>0:
#             r -= C(n-cs,k-s)
#             cs += 1
#         c.append(cs)
#         j = cs
#     return [ci-1 for ci in c]





