import inspect
from functools import cache, cached_property
from typing import Iterator, Optional, Any, Iterable, Callable
from omnibelt import extract_function_signature, extract_missing_args
from omnibelt.crafts import AbstractSkill, NestableCraft

from .abstract import AbstractConsistentGig
from .errors import GadgetFailure, MissingGadget
from .abstract import AbstractGadget, AbstractGaggle, AbstractGig


class GadgetBase(AbstractGadget):
	"""
	GadgetBase is a simple base class that adds two kinds of internal exceptions for gadgets to raise or catch as
	needed.

	Attributes:
		_GadgetFailure: The general exception that is raised when a gadget fails.
		_MissingGadgetError: The exception that is raised when a required gizmo is missing.
	"""
	_GadgetFailure = GadgetFailure
	_MissingGadgetError = MissingGadget



class AbstractGeneticGadget(AbstractGadget):
	def genes(self, gizmo: str) -> Iterator[str]:
		"""
		Returns all the gizmos that may be needed to produce the given gizmo.

		Args:
			gizmo (str): The gizmo to check.

		Returns:
			Iterator[str]: An iterator over the gizmos that are required to produce the given gizmo.
		"""
		raise NotImplementedError



class SingleGadgetBase(GadgetBase):
	"""
	SingleGadgetBase is a simple bass class for gadgets that only produce a single gizmo, which is specified at init.

	Attributes:
		_gizmo (str): The gizmo that this gadget grabs.
	"""

	def __init__(self, gizmo: str, **kwargs):
		"""
		Initializes a new instance of the SingleGadgetBase class.

		Args:
			gizmo (str): The gizmo that this gadget produces.
			**kwargs: Arbitrary keyword arguments for superclasses.
		"""
		super().__init__(**kwargs)
		self._gizmo = gizmo

	def gizmos(self) -> Iterator[str]:
		"""
		Lists the gizmo that this gadget grabs.

		Returns:
			Iterator[str]: An iterator over the gizmo that this gadget grabs.
		"""
		yield self._gizmo


	def _grab_from(self, ctx: AbstractGig):
		"""
		Grabs the gizmo from the given context. This method is called by grab_from.

		Args:
			ctx (AbstractGig): The context from which to grab the gizmo.

		Returns:
			Any: The grabbed gizmo.
		"""
		raise NotImplementedError


	def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		"""
		Returns the given gizmo from this gadget, or raises MissingGadgetError if the gizmo cannot be grabbed.

		Args:
			ctx (Optional[AbstractGig]): The context from which to grab the gizmo.
			gizmo (str): The gizmo to grab.

		Returns:
			Any: The grabbed gizmo.

		Raises:
			MissingGadgetError: If the wrong gizmo is requested.
		"""
		# if gizmo != self._gizmo: raise self._MissingGadgetError(gizmo) # would cause issues with MIMO gadgets
		return self._grab_from(ctx)



class SingleFunctionGadget(SingleGadgetBase):
	"""
	FunctionGadget is a subclass of SingleGadgetBase for gadgets that produce a single gizmo using a given function.
	The function should take a single argument, the context (gig), and return the output gizmo.

	Attributes:
		_gizmo (str): The gizmo that this gadget grabs.
		_fn (Callable[[AbstractGig], Any]): The function that this gadget uses to grab the gizmo.
	"""

	def __init__(self, gizmo: str, fn: Callable[[AbstractGig], Any], **kwargs):
		"""
		Initializes a new instance of the FunctionGadget class.

		Args:
			gizmo (str): The gizmo that this gadget produces.
			fn (Callable[[AbstractGig], Any]): The function that this gadget uses to produce the gizmo.
			**kwargs: Arbitrary keyword arguments for superclasses.
		"""
		super().__init__(gizmo=gizmo, **kwargs)
		self._fn = fn

	def __repr__(self):
		"""
		Returns a string representation of this gadget. The representation includes the class name, the function name,
		and the gizmo.

		Returns:
			str: A string representation of this gadget.
		"""
		name = getattr(self._fn, '__qualname__', None)
		if name is None:
			name = getattr(self._fn, '__name__', None)
		return f'{self.__class__.__name__}({name}: {self._gizmo})'

	@property
	def __call__(self):
		"""
		Returns the function that this gadget uses to grab the gizmo.

		Returns:
			Callable[[AbstractGig], Any]: The function that this gadget uses to grab the gizmo.
		"""
		return self._fn

	def __get__(self, instance, owner):
		"""
		Returns the function that this gadget uses to grab the gizmo. This method is used to make the gadget callable.

		Args:
			instance: The instance that the function is called on.
			owner: The owner of the instance.

		Returns:
			Callable[[AbstractGig], Any]: The function that this gadget uses to grab the gizmo.
		"""
		return self._fn.__get__(instance, owner)


	def _grab_from(self, ctx: AbstractGig) -> Any:
		"""
		Grabs the gizmo from the given context. This method is called by grab_from.

		Args:
			ctx (AbstractGig): The context from which to grab the gizmo.

		Returns:
			Any: The grabbed gizmo.
		"""
		return self._fn(ctx)


class AutoSingleFunctionGadget(SingleFunctionGadget):
	"""
	AutoFunctionGadget is a subclass of FunctionGadget that produces a single gizmo using a given function.
	The function can take any number of arguments, and any arguments that are gizmos will be grabbed from
	the gig and passed to the function automatically.
	The gizmo and the function are specified at initialization.

	Attributes:
		_gizmo (str): The gizmo that this gadget grabs.
		_fn (Callable[tuple, Any]): The function that this gadget uses to grab the gizmo.
	"""


	@staticmethod
	def _extract_gizmo_args(fn: Callable, ctx: AbstractGig, *, args: Optional[tuple] = None,
							kwargs: Optional[dict[str, Any]] = None) -> tuple[list[Any], dict[str, Any]]:
		"""
		Extracts the arguments for the function that this gadget uses to grab the gizmo. Any arguments that are gizmos
		are grabbed from the gig.

		Args:
			fn (Callable): The function that this gadget uses to produce the gizmo.
			ctx (AbstractGig): The context from which to grab any arguments needed by fn.
			args (Optional[tuple]): The positional arguments for the function passed in manually.
			kwargs (Optional[dict[str, Any]]): The keyword arguments for the function passed in manually.

		Returns:
			tuple[list[Any], dict[str, Any]]: A tuple containing a list of positional arguments and a dictionary
			of keyword arguments.
		"""
		return extract_function_signature(fn, args=args, kwargs=kwargs, default_fn=ctx.grab)


	def _grab_from(self, ctx: AbstractGig) -> Any:
		"""
		Grabs the gizmo from the given context. This method is called by grab_from.

		Args:
			ctx (AbstractGig): The context from which to grab the gizmo.

		Returns:
			Any: The grabbed gizmo.
		"""
		args, kwargs = self._extract_gizmo_args(self._fn, ctx)
		return self._fn(*args, **kwargs)



class FunctionGadget(SingleGadgetBase):
	'''the function is expected to be MISO'''
	def __init__(self, fn: Callable = None, **kwargs):
		super().__init__(**kwargs)
		self._fn = fn


	def _grab_from(self, ctx: 'AbstractGig') -> Any:
		return self._fn(ctx)


	@property
	def __call__(self):
		return self._fn



class AutoFunctionGadget(FunctionGadget, AbstractGeneticGadget):
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
		except MissingGadget:
			if param.default == param.empty:
				raise

	def _grab_from(self, ctx: 'AbstractGig') -> Any:
		# conditions = {param.name: self._find_missing_gene(ctx, param) for param in self._extract_missing_genes()}
		conditions = {}
		genes = self._extract_missing_genes()
		for param in genes:
			conditions[param.name] = self._find_missing_gene(ctx, param)
		return self._fn(**conditions)



class MIMOGadgetBase(AbstractGeneticGadget):
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


