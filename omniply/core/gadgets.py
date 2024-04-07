from typing import Iterator, Optional, Any, Iterable, Callable
from omnibelt import extract_function_signature, extract_missing_args
from omnibelt.crafts import AbstractSkill, NestableCraft

from .errors import GadgetFailure, MissingGadget
from .abstract import AbstractGadget, AbstractGaggle, AbstractGame


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


	def _grab_from(self, ctx: AbstractGame):
		"""
		Grabs the gizmo from the given context. This method is called by grab_from.

		Args:
			ctx (AbstractGame): The context from which to grab the gizmo.

		Returns:
			Any: The grabbed gizmo.
		"""
		raise NotImplementedError


	def grab_from(self, ctx: Optional[AbstractGame], gizmo: str) -> Any:
		"""
		Returns the given gizmo from this gadget, or raises MissingGadgetError if the gizmo cannot be grabbed.

		Args:
			ctx (Optional[AbstractGame]): The context from which to grab the gizmo.
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

	def __init__(self, gizmo: str, fn: Callable[[AbstractGame], Any], **kwargs):
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


	def _grab_from(self, ctx: AbstractGame) -> Any:
		"""
		Grabs the gizmo from the given context. This method is called by grab_from.

		Args:
			ctx (AbstractGame): The context from which to grab the gizmo.

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
	def _extract_gizmo_args(fn: Callable, ctx: AbstractGame, *, args: Optional[tuple] = None,
							kwargs: Optional[dict[str, Any]] = None) -> tuple[list[Any], dict[str, Any]]:
		"""
		Extracts the arguments for the function that this gadget uses to grab the gizmo. Any arguments that are gizmos
		are grabbed from the gig.

		Args:
			fn (Callable): The function that this gadget uses to produce the gizmo.
			ctx (AbstractGame): The context from which to grab any arguments needed by fn.
			args (Optional[tuple]): The positional arguments for the function passed in manually.
			kwargs (Optional[dict[str, Any]]): The keyword arguments for the function passed in manually.

		Returns:
			tuple[list[Any], dict[str, Any]]: A tuple containing a list of positional arguments and a dictionary
			of keyword arguments.
		"""
		return extract_function_signature(fn, args=args, kwargs=kwargs, default_fn=ctx.grab)


	def _grab_from(self, ctx: AbstractGame) -> Any:
		"""
		Grabs the gizmo from the given context. This method is called by grab_from.

		Args:
			ctx (AbstractGame): The context from which to grab the gizmo.

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


	def _grab_from(self, ctx: 'AbstractGame') -> Any:
		return self._fn(ctx)


	@property
	def __call__(self):
		return self._fn


