from typing import Optional, Any, Iterator, TypeVar, Generic, Union, Callable, Iterable, Mapping, Sequence, Self
from itertools import chain
from collections import OrderedDict
from omnibelt import filter_duplicates
from omnibelt.crafts import InheritableCrafty

from .abstract import AbstractGadget, AbstractGaggle, AbstractGig
from .errors import logger, GadgetFailure, MissingGadget, AssemblyError
from .gadgets import GadgetBase, SingleGadgetBase, FunctionGadget, AutoFunctionGadget


class GaggleBase(GadgetBase, AbstractGaggle):
	"""
	The GaggleBase class is a base class for creating custom gaggles. It uses a protected _gadgets_table dictionary to
	keep track of all the subgadgets, and consequently implements the expected API for gaggles.

	The gadgets should be in reverse order of presidence (so the last gadget for a given gizmo is tried first).

	Attributes:
		_gadgets_table (dict[str, list[AbstractGadget]]): A dictionary where keys are gadget names and values are lists
		of gadgets.
	"""

	_gadgets_table: dict[str, list[AbstractGadget]]  # A dictionary where keys are gadget names and values are lists of gadgets. The gadgets are kept in O-N order (reversed) for easy updates.
class GaggleBase(GadgetBase, AbstractGaggle):
	"""
	The GaggleBase class is a base class for creating custom gaggles. It uses a protected _gadgets_table dictionary to
	keep track of all the subgadgets, and consequently implements the expected API for gaggles.

	The gadgets should be in reverse order of presidence (so the last gadget for a given gizmo is tried first).

	Attributes:
	 _gadgets_table (dict[str, list[AbstractGadget]]): A dictionary where keys are gadget names and values are lists
  of gadgets.
	"""

	_gadgets_table: dict[str, list[AbstractGadget]]  # A dictionary where keys are gadget names and values are lists of gadgets. The gadgets are kept in O-N order (reversed) for easy updates.

	def __init__(self, *args, gadgets_table: Optional[Mapping] = None, **kwargs):
		"""
		Initializes a new instance of the GaggleBase class.

		Args:
			args: Variable length argument list.
			gadgets_table (Optional[Mapping]): A dictionary of gadgets. If not provided, an empty dictionary will be used.
			kwargs: Arbitrary keyword arguments.
		"""
		if gadgets_table is None:
			gadgets_table = {}
		super().__init__(*args, **kwargs)
		self._gadgets_table = gadgets_table

	def gizmos(self) -> Iterator[str]:
		"""
		Returns an iterator over the keys of the _gadgets_table dictionary.

		Returns:
			An iterator over the keys of the _gadgets_table dictionary.
		"""
		yield from self._gadgets_table.keys()

	def grabable(self, gizmo: str) -> bool:
		"""
		Checks if a gizmo is in the _gadgets_table dictionary.

		Args:
			gizmo (str): The name of the gizmo to check.

		Returns:
			bool: True if the gizmo is in the _gadgets_table dictionary, False otherwise.
		"""
		return gizmo in self._gadgets_table

	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		"""
		Returns all known gadgets that can produce the given gizmo. It iterates over local branches.

		Args:
			gizmo (Optional[str]): The name of the gizmo to check. If not provided, all gadgets are returned.

		Returns:
			Iterator[AbstractGadget]: An iterator over the gadgets that can produce the given gizmo.
		"""
		yield from self._vendors(gizmo)

	def _vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		"""
		Private method that returns all known gadgets that can produce the given gizmo.

		Args:
			gizmo (Optional[str]): The name of the gizmo to check. If not provided, all gadgets are returned.

		Returns:
			Iterator[AbstractGadget]: An iterator over the gadgets that can produce the given gizmo.
		"""
		if gizmo is None:
			for gadget in filter_duplicates(chain.from_iterable(map(reversed, self._gadgets_table.values()))):
				if isinstance(gadget, AbstractGaggle):
					yield from gadget.gadgets(gizmo)
				else:
					yield gadget
		else:
			if gizmo not in self._gadgets_table:
				raise self._MissingGadgetError(gizmo)
			for gadget in filter_duplicates(reversed(self._gadgets_table[gizmo])):
				if isinstance(gadget, AbstractGaggle):
					yield from gadget.gadgets(gizmo)
				else:
					yield gadget

	_AssemblyFailedError = AssemblyError
	def grab_from(self, ctx: AbstractGig, gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the context using the gadgets in the _gadgets_table dictionary.

		Args:
			ctx (AbstractGig): The context from which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.

		Raises:
			_AssemblyFailedError: If all gadgets fail to produce the gizmo.
			_MissingGadgetError: If no gadget can produce the gizmo.
		"""
		failures = OrderedDict()
		for gadget in self._vendors(gizmo):
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

class LoopyGaggle(GaggleBase):
	"""
	The LoopyGaggle class is a subclass of GaggleBase. It uses a protected _grabber_stack dictionary to
	keep track of all the subgadgets, and consequently implements the expected API for gaggles.

	The gadgets should be in reverse order of presidence (so the last gadget for a given gizmo is tried first).

	Attributes:
	 _grabber_stack (dict[str, Iterator[AbstractGadget]]): A dictionary where keys are gadget names and values are lists
  of gadgets.
	"""

	_grabber_stack: dict[str, Iterator[AbstractGadget]] = None

	def __init__(self, *args, grabber_stack: Optional[Mapping] = None, **kwargs):
		"""
		Initializes a new instance of the LoopyGaggle class.

		Args:
			args: Variable length argument list.
			grabber_stack (Optional[Mapping]): A dictionary of gadgets. If not provided, an empty dictionary will be used.
			kwargs: Arbitrary keyword arguments.
		"""
		if grabber_stack is None:
			grabber_stack = {}
		super().__init__(*args, **kwargs)
		self._grabber_stack = grabber_stack

	def grab_from(self, ctx: 'AbstractGig', gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the context using the gadgets in the _grabber_stack dictionary.

		Args:
			ctx (AbstractGig): The context from which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.

		Raises:
			_AssemblyFailedError: If all gadgets fail to produce the gizmo.
			_MissingGadgetError: If no gadget can produce the gizmo.
		"""
		failures = OrderedDict()
		itr = self._grabber_stack.setdefault(gizmo, self._vendors(gizmo))
		# should be the same as Kit, except the iterators are cached until the gizmo is produced
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
	The MutableGaggle class is a subclass of GaggleBase. It provides methods to include and exclude gadgets.

	The gadgets should be in reverse order of presidence (so the last gadget for a given gizmo is tried first).
	"""

	def include(self, *gadgets: AbstractGadget) -> Self:
		"""
		Adds given tools in reverse order.

		Args:
			gadgets (AbstractGadget): The gadgets to be added.

		Returns:
			Self: The instance of the class with the added gadgets.
		"""
		return self.extend(gadgets)

	def extend(self, gadgets: Iterable[AbstractGadget]) -> Self:
		"""
		Extends the _gadgets_table with the provided gadgets.

		Args:
			gadgets (Iterable[AbstractGadget]): The gadgets to be added.

		Returns:
			Self: The instance of the class with the extended gadgets.
		"""
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
		Removes the given tools, if they are found.

		Args:
			gadgets (AbstractGadget): The gadgets to be removed.

		Returns:
			Self: The instance of the class with the removed gadgets.
		"""
		for gadget in gadgets:
			for gizmo in gadget.gizmos():
				if gizmo in self._gadgets_table and gadget in self._gadgets_table[gizmo]:
					self._gadgets_table[gizmo].remove(gadget)
		return self

class CraftyGaggle(GaggleBase, InheritableCrafty):
	"""
	The CraftyGaggle class is a subclass of GaggleBase and InheritableCrafty. It provides methods to process crafts.

	The gadgets should be in reverse order of presidence (so the last gadget for a given gizmo is tried first).
	"""

	def _process_crafts(self):
		"""
		Processes the crafts. It groups the crafts by where the craft is defined and converts crafts to skills and adds
		them in O-N (N-O) order to table.
		"""
		# group by where the craft is defined
		history = OrderedDict() # src<N-O> : craft<N-O>
		for src, key, craft in self._emit_all_craft_items(): # craft<N-O>
			history.setdefault(src, []).append(craft)

		# convert crafts to skills and add in O-N (N-O) order to table
		for crafts in reversed(history.values()): # O-N
			gizmos = {}
			for craft in reversed(crafts): # N-O (in order of presidence)
				skill = craft.as_skill(self)
				for gizmo in skill.gizmos():
					gizmos.setdefault(gizmo, []).append(skill)
			for gizmo, skills in gizmos.items():
				self._gadgets_table.setdefault(gizmo, []).extend(reversed(skills)) # O-N (in order of appearance)












