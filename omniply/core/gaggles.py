from typing import Optional, Any, Iterator, TypeVar, Generic, Union, Callable, Iterable, Mapping, Sequence, Self
from itertools import chain
from collections import OrderedDict
from omnibelt import filter_duplicates
from omnibelt.crafts import InheritableCrafty

from .abstract import AbstractGadget, AbstractGaggle, AbstractGame
from .errors import logger, GadgetFailure, MissingGadget, AssemblyError
from .gadgets import GadgetBase, SingleGadgetBase, SingleFunctionGadget, AutoSingleFunctionGadget



class GaggleBase(GadgetBase, AbstractGaggle):
	"""
	The GaggleBase class is a base class for creating custom gaggles. It uses a protected _gadgets_table dictionary to
	keep track of all the subgadgets, and consequently implements the expected API for gaggles.

	The gadgets in the table should be in O-N order (reverse order of presidence, so the last gadget in the list for
	a gizmo is tried first).

	Attributes:
		_gadgets_table (dict[str, list[AbstractGadget]]): A dictionary where keys are gadget names and values are lists
		of subgadgets.
	"""

	_gadgets_table: dict[str, list[AbstractGadget]]
	_gadgets_list: list[AbstractGadget]

	def __init__(self, *args, **kwargs):
		"""
		Initializes a new instance of the GaggleBase class.

		Args:
			args: unused
			gadgets_table (Optional[Mapping]): A dictionary of gadgets. If not provided, defauls to an empty dictionary.
			kwargs: Arbitrary keyword arguments.
		"""
		super().__init__(*args, **kwargs)
		self._gadgets_table = {}
		self._gadgets_list = []

	def gizmos(self) -> Iterator[str]:
		"""
		Iterates over all known gizmos that this gaggle can produce in order of oldest to newest.
		"""
		yield from self._gadgets_table.keys()

	def gives(self, gizmo: str) -> bool:
		"""
		Checks if a gizmo is can be produced by this gaggle.

		Args:
			gizmo (str): The name of the gizmo to check.

		Returns:
			bool: True if the gizmo can be produced, False otherwise.
		"""
		return gizmo in self._gadgets_table

	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		"""
		Returns all known subgadgets that are used by this gaggle wihtout repeats, that produces the specified gizmo,
		if provided, otherwise, iterates over all subgadgets. The iteration starts with the most recently added gadgets.

		Args:
			gizmo (Optional[str]): The name of the gizmo to check. If not provided, all gadgets are returned.

		Returns:
			Iterator[AbstractGadget]: An iterator over the gadgets that can produce the given gizmo.
		"""
		yield from self._vendors(gizmo)

	def _vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		"""
		Private method that returns all known subgadgets that can produce the given gizmo.

		Args:
			gizmo (Optional[str]): The name of the gizmo to check. If not provided, all gadgets are returned.

		Returns:
			Iterator[AbstractGadget]: An iterator over the gadgets that can produce the given gizmo.
		"""
		if gizmo is None:
			yield from reversed(self._gadgets_list)
		else:
			if gizmo not in self._gadgets_table:
				raise self._MissingGadgetError(gizmo)
			yield from reversed(self._gadgets_table[gizmo])


	def _gadgets(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		"""
		Private method that returns all known subgadgets that can produce the given gizmo.

		Args:
			gizmo (Optional[str]): The name of the gizmo to check. If not provided, all gadgets are returned.

		Returns:
			Iterator[AbstractGadget]: An iterator over the gadgets that can produce the given gizmo.
		"""
		for vendor in self._vendors(gizmo):
			if isinstance(vendor, AbstractGaggle):
				yield from vendor.gadgets(gizmo)
			else:
				yield vendor


	_AssemblyFailedError = AssemblyError
	def grab_from(self, ctx: AbstractGame, gizmo: str) -> Any:
		"""
		Tries to grab a gizmo using the subgadgets given the context.

		Args:
			ctx (AbstractGame): The context with which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.

		Raises:
			AssemblyFailedError: If all subgadgets fail to produce the gizmo.
			MissingGadgetError: If no gadget can produce the gizmo.
		"""
		failures = OrderedDict()
		for gadget in self._gadgets(gizmo):
			try:
				return gadget.grab_from(ctx, gizmo)
			except self._GadgetFailure as e:
				failures[e] = gadget
			except:
				logger.debug(f'{gadget!r} failed while trying to produce {gizmo!r}')
				raise
		if failures:
			raise self._AssemblyFailedError(failures)
		raise self._MissingGadgetError(gizmo)



class MultiGadgetBase(AbstractGaggle):
	"""
	MultiGadgetBase is a special kind of gaggle that hides all sub-gadgets from being accessed through `gadgets()`
	and `vendors()`. Instead, it presents itself as a gadget that can produce all the products of the sub-gadgets.

	Generally, if you know before runtime what gizmos a gadget can produce, then it should just be a gadget, however,
	if you want to be able to dynamically add sub-gadgets, while still preventing delegation, then you can use this.

	"""
	def gadgets(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		"""
		Lists all known gadgets under this multi-gadget that can produce the given gizmo.
		Since this is a multi-gadget, it doesn't delegate to sub-gadgets, and instead yields itself.

		Args:
			gizmo (Optional[str]): If specified, yields only the gadgets that can produce this gizmo. In this case, it
			has no effect.

		Returns:
			Iterator[AbstractGadget]: An iterator over the known gadgets in this multi-gadget that can produce the
			specified gizmo. Since this is a multi-gadget, it yields only itself.
		"""
		yield self

	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		"""
		Lists all known sub-gadgets and sub-gaggles in this multi-gadget that can produce the given gizmo.
		Since this is a multi-gadget, it doesn't delegate to sub-gadgets, and instead yields itself.

		Args:
			gizmo (Optional[str]): If specified, yields only the gadgets that can produce this gizmo. In this case, it
			checks if this multi-gadget can produce the gizmo.

		Returns:
			Iterator[AbstractGadget]: An iterator over the known gadgets that can directly produce the given gizmo. Since
			this is a multi-gadget, it yields itself.
		"""
		yield self



class LoopyGaggle(GaggleBase):
	"""
	The LoopyGaggle class is mix-in for custom gaggles that allows multiple gadgets that produce the same gizmos to
	recursively call each other. Specifically, if a subgadget requires the same gizmo as input as it produces, then the
	next known subgadget of this gaggle is used after which the stack is resolved.

	Attributes:
		_grabber_stack (dict[str, Iterator[AbstractGadget]]): A dictionary keeping track of which subgadgets are still
		available to use for each gizmo.
	"""
	_grabber_stack: dict[str, Iterator[AbstractGadget]] = None

	def __init__(self, *args, **kwargs):
		"""
		Initializes a new instance of the LoopyGaggle class.

		Args:
			args: unused, passed to super.
			kwargs: unused, passed to super.
		"""
		super().__init__(*args, **kwargs)
		self._grabber_stack = {}

	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the context using the gadgets in the _grabber_stack dictionary.

		Args:
			ctx (AbstractGame): The context with which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.

		Raises:
			AssemblyFailedError: If all gadgets fail to produce the gizmo.
			MissingGadgetError: If no gadget can produce the gizmo.
		"""
		failures = OrderedDict()
		itr = self._grabber_stack.setdefault(gizmo, self._gadgets(gizmo))
		for gadget in itr:
			try:
				out = gadget.grab_from(ctx, gizmo)
			except self._GadgetFailure as e:
				failures[e] = gadget
			except:
				logger.debug(f'{gadget!r} failed while trying to produce {gizmo!r}')
				raise
			else:
				if gizmo in self._grabber_stack:
					self._grabber_stack.pop(gizmo)
				return out
		if gizmo in self._grabber_stack:
			self._grabber_stack.pop(gizmo)
		if failures:
			raise self._AssemblyFailedError(failures)
		raise self._MissingGadgetError(gizmo)

class MutableGaggle(GaggleBase):
	"""
	The MutableGaggle class is a mix-in for custom gaggles to dynamically add and remove subgadgets.
	"""

	def include(self, *gadgets: AbstractGadget) -> Self:
		"""
		Adds given gadgets in the order that is given, which means subsequent `grab` would use the first provided
		gadget before trying the next.

		Args:
			gadgets (AbstractGadget): The gadgets to be added.

		Returns:
			Self: this gaggle.
		"""
		return self.extend(gadgets)

	def extend(self, gadgets: Iterable[AbstractGadget]) -> Self:
		"""
		Adds given gadgets in the iterator in the order that is given, which means subsequent `grab` would use the
		first provided gadget before trying the next.

		Args:
			gadgets (Iterable[AbstractGadget]): The gadgets to be added.

		Returns:
			Self: this gaggle.
		"""
		self._gadgets_list.extend(reversed(gadgets))
		new = {}
		for gadget in gadgets:
			for gizmo in gadget.gizmos():
				new.setdefault(gizmo, []).append(gadget)
		for gizmo, gadgets in new.items():
			if gizmo in self._gadgets_table:
				for gadget in gadgets:
					if gadget in self._gadgets_table[gizmo]:
						self._gadgets_table[gizmo].remove(gadget)
			self._gadgets_table.setdefault(gizmo, []).extend(reversed(gadgets))
		return self

	def exclude(self, *gadgets: AbstractGadget) -> Self:
		"""
		Removes the given gadgets, if they are found.

		Args:
			gadgets (AbstractGadget): The gadgets to be removed.

		Returns:
			Self: this gaggle.
		"""
		for gadget in gadgets:
			for gizmo in gadget.gizmos():
				if gizmo in self._gadgets_table and gadget in self._gadgets_table[gizmo]:
					self._gadgets_table[gizmo].remove(gadget)
			if gadget in self._gadget_list:
				self._gadgets_list.remove(gadget)
		return self

class CraftyGaggle(GaggleBase, InheritableCrafty):
	"""
	The CraftyGaggle class is a mix-in for custom gaggles to handle crafts such as `tool`.

	Note that in order to procuess and add all found crafts, a subclass must call `_process_crafts()`, which is not
	done here.
	"""

	def _process_crafts(self):
		"""
		Identifies all crafts contained in the class (including super classes) that are gadgets and adds those as
		subgadgets, in the order in which they are defined.

		Note that, in order to be processed correctly, the crafts should produce skills which are instances of
		`AbstractGadget`.
		"""
		# gate by where the craft is defined
		history = OrderedDict() # src<N-O> : craft<N-O>
		for src, key, craft in self._emit_all_craft_items(): # craft<N-O>
			history.setdefault(src, []).append(craft)

		# convert crafts to skills and add in O-N (N-O) order to table
		for crafts in reversed(history.values()): # O-N
			gizmos = {}
			for craft in reversed(crafts): # N-O (in order of precedence)
				skill = craft.as_skill(self) # TODO: convert as_skill to a generator to enable multiple skills per craft
				if isinstance(skill, AbstractGadget):
					for gizmo in skill.gizmos():
						gizmos.setdefault(gizmo, []).append(skill)
					self._gadgets_list.append(skill) # O-N (in order of appearance)
				else:
					self._process_auxiliary_skill(skill)
			for gizmo, skills in gizmos.items():
				self._gadgets_table.setdefault(gizmo, []).extend(reversed(skills)) # O-N (in order of appearance)


	def _process_auxiliary_skill(self, skill):
		pass

