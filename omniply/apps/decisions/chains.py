from .imports import *

from ...core.games import CacheGame, GaggleBase

from .abstract import (AbstractDecidable, AbstractChain, AbstractCase, AbstractDecision, AbstractGadgetDecision,
					   AbstractIndexDecision, CHOICE, AbstractCountableDecision)
from .errors import IgnoreCase



class ConsiderableDecision(AbstractDecision):
	'''
	these decisions respond to `consider` and should generally be pretty high in the mro to enable defaulting
	'''
	_IgnoreCase = IgnoreCase
	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
		if isinstance(ctx, AbstractCase) and gizmo == self.choice_gizmo:
			try:
				return ctx.check(self)
			except self._IgnoreCase:
				pass
		return super().grab_from(ctx, gizmo)



class SimpleCase(CacheGame, AbstractCase):
	def __init__(self, chain: AbstractChain, cache: dict[str, Any] = None, **kwargs):
		cache = cache or {}
		super().__init__(**kwargs)
		self._chain = chain
		self.data.update(cache)


	def check(self, decision: AbstractDecision) -> CHOICE:
		return self._chain.confirm(self, decision)



class Chain(AbstractChain):
	def __init__(self, source: AbstractDecidable, targets: Iterable[str], cache: dict[str, Any] = None, **kwargs):
		super().__init__(**kwargs)
		self._source = source
		self._targets = targets
		self._prior_cache = cache
		self._current = None
		self._completed = False
		self._chain_stack = []
		self._waiting_chains = {}
		self._chain_cache = {}


	@property
	def current(self):
		return self._current


	def _create_case(self, cache: dict[str, Any]) -> AbstractCase:
		case = self._source.create_case(cache, chain=self)
		for target in self._targets:
			case.grab(target)
		return case


	def __next__(self):
		if self._current is None:
			# seed the initial case to populate the stack with any decisions that have to made
			self._current = self._create_case(self._prior_cache)
			return self._current

		for gizmo in reversed(self._chain_stack):
			for choice in self._waiting_chains[gizmo]:
				self._chain_cache[gizmo] = choice
				self._current = self._create_case({**self._chain_cache, **self._prior_cache})
				return self._current
			else:
				self._chain_stack.pop()
				self._waiting_chains.pop(gizmo)
				self._chain_cache.pop(gizmo)

		self._completed = True
		raise StopIteration


	@staticmethod
	def _decision_sampling(decision: AbstractDecision, case: AbstractCase) -> Iterator[CHOICE]:
		'''default sampling strategy'''
		yield from decision.choices(case)


	_IgnoreCase = IgnoreCase
	def confirm(self, case: AbstractCase, decision: AbstractDecision) -> CHOICE:
		if self._completed:
			raise self._IgnoreCase()
		# if you are confirming, it must be a NEW decision requiring expansion
		gizmo = decision.choice_gizmo
		assert gizmo not in self._waiting_chains, f'Decision {gizmo} was already made (should have been cached)'
		if gizmo in self._prior_cache: # decision has been made pre-chain
			return self._prior_cache[gizmo]
		self._chain_stack.append(gizmo)
		self._waiting_chains[gizmo] = self._decision_sampling(decision, case)
		# a decision should be guaranteed to have at least one choice
		choice = next(self._waiting_chains[gizmo])
		self._chain_cache[gizmo] = choice
		return choice



class CarefulChain(Chain):
	def __init__(self, source: AbstractDecidable, targets: Iterable[str], cache: dict[str, Any] = None,
				 limit: int = None, **kwargs):
		super().__init__(source, targets, cache=cache, **kwargs)
		self._limit = limit


	def _decision_sampling(self, decision: AbstractDecision, case: AbstractCase) -> Iterator[CHOICE]:
		'''default sampling strategy'''
		if (self._limit is not None and isinstance(decision, AbstractCountableDecision)
				and decision.count(case) > self._limit):
			yield from decision.cover(self._limit, case)
		else:
			yield from super()._decision_sampling(decision, case)



class DeciderBase(CacheGame, AbstractDecidable):
	_Case: type[SimpleCase] = None
	_Chain = Chain
	def consider(self, *targets: str) -> Chain:
		cache = {gizmo: self[gizmo] for gizmo in self.cached()}
		return self._Chain(self, targets, cache=cache)


	def create_case(self, cache: dict[str, Any] = None, chain: AbstractChain = None) -> AbstractCase:
		return self._Case(chain=chain, cache=cache)


class CarefulDecider(DeciderBase):
	_Chain = CarefulChain
	def consider(self, *targets: str, limit: int = None) -> CarefulChain:
		'''
		limit refers to the maximum number of choices to consider for any given decision
		'''
		cache = {gizmo: self[gizmo] for gizmo in self.cached()}
		return self._Chain(self, targets, cache=cache, limit=limit)



class CertificateGaggle(CacheGame, GaggleBase):
	def certificate(self) -> dict[str, CHOICE]:
		return {gizmo: self[gizmo] for gizmo in self.cached()
				if any(gizmo == decision.choice_gizmo for decision in self._gadgets(gizmo)
					   if isinstance(decision, AbstractDecision))}



# `contemplate` - advanced version of `consider` which can handle custom sampling strategies
#   or skipping specific choices or cases



class NaiveConsiderationBase(AbstractDecidable):
	def _create_case(self, cache: dict[str, Any]) -> AbstractGame:
		raise NotImplementedError


	def _consider(self, *, targets: Iterable[str], cache: dict[str, Any],
				  get_gadgets: Callable[[str], Iterator[AbstractGadget]],
				  resolved: set[str]) -> Iterator[AbstractGame]:
		'''top-down - requires guarantee that only the targets will be grabbed'''
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




