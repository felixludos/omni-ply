from .imports import *

from .abstract import AbstractDecision, AbstractGadgetDecision, CHOICE
from .decisions import LargeDecision, SimpleDecisionBase, DynamicDecision, SelfSelectingDecision, GadgetDecisionBase
from .chains import ConsiderableDecision, DeciderBase, NaiveConsiderationBase



class OldController(Context, NaiveConsiderationBase):
	def certificate(self) -> dict[str, CHOICE]:
		return {gizmo: self[gizmo] for gizmo in self.cached()
				if any(gizmo == decision.choice_gizmo for decision in self._gadgets(gizmo)
					   if isinstance(decision, AbstractDecision))}


	def _create_case(self, cache: dict[str, Any]) -> AbstractGame:
		case = self.gabel()
		case.data.update(cache)
		# case.include(DictGadget(cache.copy()))
		return case

	def consider(self, *targets: str) -> Iterator[AbstractGame]:
		given = {gizmo: self[gizmo] for gizmo in self.cached()}
		yield from self._consider(targets=targets, resolved=set(given.keys()), cache=dict(given),
								  get_gadgets=self._gadgets)



class GadgetDecision(ConsiderableDecision, DynamicDecision, SelfSelectingDecision, GadgetDecisionBase):
	pass



class SimpleDecision(ConsiderableDecision, SimpleDecisionBase):
	def __init__(self, gizmo: str, choices: Iterable[Any] | Mapping[str, Any] = None, **kwargs):
		if choices is None:
			choices = {}
		if not isinstance(choices, Mapping):
			choices = {i: choice for i, choice in enumerate(choices)}
		super().__init__(gizmo=gizmo, **kwargs)
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



class Permutation(ConsiderableDecision, LargeDecision, SimpleDecisionBase):
	'''
	Returns a random permutation of N objects as a tuple of indices.
	'''
	def __init__(self, N: int, **kwargs):
		super().__init__(**kwargs)
		self.N = N


	def count(self, ctx: 'AbstractGame' = None, gizmo: str = None) -> int:
		'''how many choices are available'''
		return (self.N + 1) * self.N // 2


	@staticmethod
	def _choice_to_permutation(index: int, N: int) -> list[int]:
		"""
		Convert an integer to a permutation of N objects in pure Python.

		(by ChatGPT4)

		Parameters:
		- index: The given integer representing the specific ordering.
		- N: The number of distinct objects.

		Returns:
		- A list containing the indices for each element to arrange the objects into the specified ordering.
		"""
		# Compute factoradic representation
		factoradic = []
		for i in range(1, N + 1):
			index, remainder = divmod(index, i)
			factoradic.append(remainder)

		# Reverse it for direct use
		factoradic.reverse()

		# Generate permutation
		elements = list(range(N))  # Elements to permute
		permutation = []
		for f in factoradic:
			permutation.append(elements.pop(f))

		return permutation


	def _commit(self, ctx: 'AbstractGame', choice: CHOICE, gizmo: str) -> tuple[Any, ...]:
		return tuple(self._choice_to_permutation(choice, self.N))



class Combination(ConsiderableDecision, LargeDecision, SimpleDecisionBase):
	'''
	Returns a random combination of K objects from N objects as a tuple of indices.
	'''
	def __init__(self, N: int, K: int, **kwargs):
		super().__init__(**kwargs)
		self.N = N
		self.K = K


	def count(self, ctx: 'AbstractGame' = None, gizmo: str = None) -> int:
		'''how many choices are available'''
		return math.comb(self.N, self.K)


	@staticmethod
	def _choice_to_combination(index: int, n: int, k: int) -> list[int]:
		"""
		returns the i-th combination of k numbers chosen from 0,1,2,...,n-1

		adapted from https://math.stackexchange.com/questions/1227409/indexing-all-combinations-without-making-list
		"""
		mx = math.comb(n, k)
		assert 0 <= index <= mx, f"index={index} must be in [0, {mx}]"
		c = []
		r = index
		j = 0
		for s in range(1, k + 1):
			cs = j + 1
			while r - math.comb(n - cs, k - s) > 0:
				r -= math.comb(n - cs, k - s)
				cs += 1
			c.append(cs - 1)
			j = cs
		return c


	def _commit(self, ctx: 'AbstractGame', choice: CHOICE, gizmo: str) -> tuple[Any, ...]:
		return tuple(self._choice_to_combination(choice, self.N, self.K))


