from typing import Iterator, Callable, Optional, Any, Iterable
import inspect
from functools import cache, cached_property
from omnibelt import extract_missing_args

from .errors import GrabError
from .abstract import AbstractGenetic, AbstractConsistentGig, AbstractGig
from .gadgets import FunctionGadget



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

	def genes(self, gizmo: str) -> Iterator[str]:
		for param in self._extract_missing_genes():
			yield self._arg_map.get(param.name, param.name)

	def _find_missing_gene(self, ctx: 'AbstractGig', param: inspect.Parameter) -> dict[str, Any]:
		try:
			return ctx.grab(self._arg_map.get(param.name, param.name))
		except GrabError:
			if param.default == param.empty:
				raise
			return param.default

	def _grab_from(self, ctx: 'AbstractGig') -> Any:
		# conditions = {param.name: self._find_missing_gene(ctx, param) for param in self._extract_missing_genes()}
		conditions = {}
		genes = self._extract_missing_genes()
		for param in genes:
			conditions[param.name] = self._find_missing_gene(ctx, param)
		return self._fn(**conditions)



class MIMOGadgetBase(AbstractGenetic):
	'''if `gizmos` is specified then the function is expected to give multiple outputs
	these must be returned as a dict (with the gizmos as keys) or a tuple (with the gizmos in the same order)'''

	def __eq__(self, other):
		raise NotImplementedError


	def __hash__(self):
		raise NotImplementedError


	def _multi_output_order(self, gizmo: str):
		raise NotImplementedError


	def _grab_from_multi_output(self, ctx: Optional[AbstractGig], gizmo: str) -> dict[str, Any]:
		if not isinstance(ctx, AbstractConsistentGig):
			raise TypeError(f'Cannot use MIMOFunctionGadget with non-consistent gig')

		reqs = list(self.genes(gizmo))

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


	def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		if self._multi_output_order(gizmo) is None:
			return super().grab_from(ctx, gizmo)
		return self._grab_from_multi_output(ctx, gizmo)



class AutoMIMOFunctionGadget(MIMOGadgetBase, AutoFunctionGadget):
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


	def gizmos(self) -> Iterator[str]:
		if self._multi_output_order() is None:
			yield self._gizmo
		else:
			yield from self._gizmo



from omnibelt.crafts import NestableCraft, AbstractCraft, AbstractSkill
from .gaggles import CraftyGaggle
from .tools import SkillBase, CraftBase



class GenomeSkill(SkillBase):
	pass


class GenomeCraft(NestableCraft):



	pass



class GeneticCrafty(CraftyGaggle, AbstractGenetic):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._genome_table = {}


	def _process_auxiliary_skill(self, skill):
		super()._process_auxiliary_skill(skill)
		if isinstance(skill, GenomeSkill):
			pass


	def genes(self, gizmo: str) -> Iterator[str]:
		if gizmo in self._genome_table:
			yield from self._genome_table[gizmo].genes(gizmo)


class GenomeDecorator(NestableCraft):
	def __init__(self, gizmo: str):
		self.gizmo = gizmo

	def __call__(self, fn):
		fn._gene_decorator = self
		return fn

	def __get__(self, instance, owner):
		if instance is None:
			return self
		return self.__class__(self.gizmo, self.arg)

	def __set_name__(self, owner, name):
		self.name = name

	def __set__(self, instance, value):
		setattr(instance, self.name, value)

	def __get__(self, instance, owner):
		if instance is None:
			return self
		return getattr(instance, self.name)




















