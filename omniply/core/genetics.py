from typing import Iterator, Callable, Optional, Any, Iterable
import inspect
from functools import cache, cached_property
from omnibelt import extract_missing_args
from omnibelt.crafts import NestableCraft, AbstractCrafty

from .errors import GrabError
from .abstract import AbstractConsistentGame, AbstractGame, AbstractGadget, AbstractGaggle
from .gadgets import FunctionGadget, GadgetBase
from .gaggles import GaggleBase


# from .gaggles import CraftyGaggle
# from .tools import SkillBase, CraftBase



class AbstractGene:
	@property
	def name(self) -> str:
		raise NotImplementedError

	@property
	def source(self) -> AbstractGadget:
		raise NotImplementedError

	@property
	def endpoint(self):
		return self.source.grab_from

	@property
	def parents(self) -> tuple:
		raise NotImplementedError

	@property
	def siblings(self) -> tuple:
		'''returns the siblings in order with the space for self set to None'''
		raise NotImplementedError

	def alternatives(self) -> Iterator['AbstractGadget']:
		raise NotImplementedError



class AbstractGenetic(AbstractGadget):
	def genes(self, gizmo: str) -> Iterator[AbstractGene]:
		"""
		Returns all the gizmos that may be needed to produce the given gizmo.

		Args:
			gizmo (str): The gizmo to check.

		Returns:
			Iterator[str]: An iterator over the gizmos that are required to produce the given gizmo.
		"""
		raise NotImplementedError


class Gene(AbstractGene):
	def __init__(self, name: str, source: AbstractGadget, parents: Iterable[str] = None, siblings: Iterable[str] = None,
				 endpoint: Callable = None):
		if siblings is not None:
			siblings = tuple(None if sibling == name else sibling for sibling in siblings)
		if parents is not None:
			parents = tuple(parents)
		self._name = name
		self._source = source
		self._parents = parents
		self._siblings = siblings
		self._endpoint = endpoint

	def __str__(self):
		args = f'{", ".join(self.parents)}' if len(self.parents) else '⋅'
		return f'{self.name} ← {args}'

	def __repr__(self):
		return str(self)

	def __hash__(self):
		return hash((self.name, self.source, self.endpoint))

	def __eq__(self, other):
		return (isinstance(other, Gene) and self.name == other.name
				and self.source == other.source and self.endpoint == other.endpoint)

	@property
	def name(self) -> str:
		return self._name

	@property
	def source(self) -> AbstractGadget:
		return self._source

	@property
	def parents(self) -> tuple:
		return self._parents

	@property
	def siblings(self) -> tuple:
		return self._siblings

	@property
	def endpoint(self):
		return self._endpoint

	def __iter__(self):
		yield from self.parents

	def __len__(self):
		return len(self.parents)



class GeneticBase(AbstractGenetic):
	_Gene = Gene


	def _genetic_information(self, gizmo: str):
		return {'name': gizmo, 'gadget': self}


	def genes(self, gizmo: str) -> AbstractGene:
		return self._Gene(**self._genetic_information(gizmo))



class GeneticGadget(GeneticBase, GadgetBase):
	pass



class GeneticGaggle(GaggleBase, AbstractGenetic):
	def genes(self, gizmo: str) -> AbstractGene:
		for vendor in self._gadgets(gizmo):
			if isinstance(vendor, AbstractGenetic):
				yield from vendor.genes(gizmo)



class AutoFunctionGadget(FunctionGadget, AbstractGenetic):
	def __init__(self, fn: Callable = None, gizmo: str = None, arg_map: dict[str, str] = None, **kwargs):
		if arg_map is None:
			arg_map = {}
		super().__init__(gizmo=gizmo, fn=fn, **kwargs)
		self._arg_map = arg_map

	@cache
	def _extract_missing_genes(self, fn=None, args=None, kwargs=None):
		if fn is None:
			fn = self.__call__
		fn = fn.__func__ if isinstance(fn, (classmethod, staticmethod)) else fn
		return extract_missing_args(fn, args=args, kwargs=kwargs, skip_first=isinstance(fn, classmethod))

	_Gene = Gene
	def genes(self, gizmo: str) -> Iterator[AbstractGene]:
		parents = [self._arg_map.get(param.name, param.name) for param in self._extract_missing_genes()]
		yield self._Gene(gizmo, self, parents=tuple(parents), endpoint=self._fn)

	def _find_missing_gene(self, ctx: 'AbstractGame', param: inspect.Parameter) -> dict[str, Any]:
		try:
			return ctx.grab(self._arg_map.get(param.name, param.name))
		except GrabError:
			if param.default == param.empty:
				raise
			return param.default

	def _grab_from(self, ctx: 'AbstractGame') -> Any:
		# conditions = {param.name: self._find_missing_gene(ctx, param) for param in self._extract_missing_genes()}
		conditions = {}
		genes = self._extract_missing_genes()
		for param in genes:
			conditions[param.name] = self._find_missing_gene(ctx, param)
		return self._fn(**conditions)



class MIMOGadgetBase(FunctionGadget, AbstractGenetic):
	'''if `gizmos` is specified then the function is expected to give multiple outputs
	these must be returned as a dict (with the gizmos as keys) or a tuple (with the gizmos in the same order)'''

	def __init__(self, fn: Callable = None, gizmos: Iterable[str] = None, gizmo: str = None, **kwargs):
		assert (gizmo is None) != (gizmos is None), f'Cannot specify both gizmo and gizmos: {gizmo}, {gizmos}'
		super().__init__(fn=fn, gizmo=tuple(gizmos) if gizmo is None else gizmo, **kwargs)

	def __eq__(self, other):
		return isinstance(other, AutoMIMOFunctionGadget) and self._fn == other._fn and self._gizmo == other._gizmo


	def __hash__(self):
		return hash((self._fn, self._gizmo))

	# @cache # TODO: does this matter for performance?
	def _multi_output_order(self, gizmo: str = None):
		if isinstance(self._gizmo, tuple):
			return self._gizmo


	def _grab_from_multi_output(self, ctx: Optional[AbstractGame], gizmo: str) -> dict[str, Any]:
		if not isinstance(ctx, AbstractConsistentGame):
			raise TypeError(f'Cannot use MIMOFunctionGadget with non-consistent game')

		reqs = list(next(self.genes(gizmo)).parents)

		if all(ctx.is_unchanged(gene) for gene in reqs):
			cache = ctx.check_gadget_cache(self)
			if gizmo in cache:
				return cache[gizmo]
			elif len(cache):
				raise NotImplementedError(f'Cache should either be empty or contain all gizmos, got {cache.keys()}')

		out = super().grab_from(ctx, gizmo)
		order = self._multi_output_order(gizmo)

		assert isinstance(out, (dict, tuple)), f'Expected MIMO function to return dict or tuple, got {type(out)}'
		if isinstance(out, tuple):
			assert len(out) == len(order), (f'Expected MIMO function to return tuple of length '
												  f'{len(order)}, got {len(out)}')
			out = dict(zip(order, out))
		assert all(g in out for g in order), (f'Expected MIMO function to return dict with keys '
													f'{order}, got {out.keys()}')

		ctx.update_gadget_cache(self, out)
		return out[gizmo]


	def grab_from(self, ctx: Optional[AbstractGame], gizmo: str) -> Any:
		if self._multi_output_order(gizmo) is None:
			return super().grab_from(ctx, gizmo)
		return self._grab_from_multi_output(ctx, gizmo)


	def gizmos(self) -> Iterator[str]:
		if self._multi_output_order() is None:
			yield self._gizmo
		else:
			yield from self._gizmo



class AutoMIMOFunctionGadget(MIMOGadgetBase, AutoFunctionGadget):
	# def __init__(self, fn: Callable = None, gizmos: Iterable[str] = None, gizmo: str = None, **kwargs):
	# 	assert (gizmo is None) != (gizmos is None), f'Cannot specify both gizmo and gizmos: {gizmo}, {gizmos}'
	# 	super().__init__(fn=fn, gizmo=tuple(gizmos) if gizmo is None else gizmo, **kwargs)


	def genes(self, gizmo: str) -> Iterator[AbstractGene]:
		parents = [self._arg_map.get(param.name, param.name) for param in self._extract_missing_genes()]
		siblings = self._multi_output_order(gizmo)
		if siblings is not None:
			siblings = tuple(sibling if sibling != gizmo else None for sibling in siblings)
		yield self._Gene(gizmo, self, parents=tuple(parents), siblings=siblings, endpoint=self._fn)



class Parentable(NestableCraft):
	def __init__(self, *args, parents: tuple = None, **kwargs):
		super().__init__(*args, **kwargs)
		self._parents = parents
		self._parents_fn = None


	def parents(self, fn: Callable[[], Iterable[str]]) -> Callable:
		assert self._parents is None, f'Parents have already been specified ({self._parents})'
		self._parents_fn = fn
		return fn

	def as_skill(self, owner: AbstractCrafty):
		skill: ParentedSkill = super().as_skill(owner)
		skill._set_parents(self._parents)
		if self._parents_fn is not None:
			fn = self._parents_fn.__get__(owner, type(owner))
			skill._set_parents_fn(fn)
		return skill

class ParentedSkill(AbstractGenetic):
	def get_parents(self):
		if self._parents is not None:
			return tuple(self._parents)
		elif self._parents_fn is not None:
			return tuple(self._parents_fn())

	_parents = None
	def _set_parents(self, parents: tuple):
		self._parents = parents

	_parents_fn = None
	def _set_parents_fn(self, fn: Callable[[], Iterable[str]]):
		self._parents_fn = fn














