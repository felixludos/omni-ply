from .imports import *

from .abstract import AbstractDecidable, AbstractChain, AbstractCase, AbstractDecision, AbstractGadgetDecision
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



class SimpleCase(AbstractCase):
	pass




class SimpleChain(AbstractChain):
	def __init__(self, source: AbstractGame, targets: Iterable[str], prior: dict[str, Any] = None, **kwargs):
		super().__init__(**kwargs)
		self.targets = targets
		self.prior = prior or {}
		self._current = None
		self._source = source
		self._chain_stack = list(targets)
		self._waiting_chains = {}
		self._chain_cache = {}

	_Case = None
	def _create_case(self, prior: dict[str, Any]) -> AbstractGame:
		return self._Case(self, prior)


	def __next__(self):
		return self._create_case(self.prior)




class DeciderBase(AbstractDecidable):
	pass



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




