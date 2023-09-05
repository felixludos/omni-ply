from typing import Optional, Any, Iterator, TypeVar, Generic, Union, Callable, Iterable, Mapping, Sequence, Self
from itertools import chain
from collections import OrderedDict
from omnibelt import filter_duplicates
from omnibelt.crafts import InheritableCrafty

from .abstract import AbstractGadget, AbstractGaggle, AbstractGig
from .errors import logger, GadgetError, MissingGizmo, AssemblyError
from .gadgets import GadgetBase, SingleGadgetBase, FunctionGadget, AutoFunctionGadget



class GaggleBase(GadgetBase, AbstractGaggle):
	_gadgets_table: dict[str, list[AbstractGadget]] # tools are kept in O-N order (reversed) for easy updates

	def __init__(self, *args, gadgets_table: Optional[Mapping] = None, **kwargs):
		if gadgets_table is None:
			gadgets_table = {}
		super().__init__(*args, **kwargs)
		self._gadgets_table = gadgets_table


	def gizmos(self) -> Iterator[str]:
		yield from self._gadgets_table.keys()


	def grabable(self, gizmo: str) -> bool:
		return gizmo in self._gadgets_table


	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		'''returns all known gadgets that can produce the given gizmo (iterates over local branches)'''
		yield from self._vendors(gizmo)


	def _vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		if gizmo is None:
			for gadget in filter_duplicates(chain.from_iterable(map(reversed, self._gadgets_table.values()))):
				if isinstance(gadget, AbstractGaggle):
					yield from gadget.gadgets(gizmo)
				else:
					yield gadget
		else:
			if gizmo not in self._gadgets_table:
				raise self._MissingGizmoError(gizmo)
			for gadget in filter_duplicates(reversed(self._gadgets_table[gizmo])):
				if isinstance(gadget, AbstractGaggle):
					yield from gadget.gadgets(gizmo)
				else:
					yield gadget


	_AssemblyFailedError = AssemblyError
	def grab_from(self, ctx: AbstractGig, gizmo: str) -> Any:
		failures = OrderedDict()
		for gadget in self._vendors(gizmo):
			try:
				return gadget.grab_from(ctx, gizmo)
			except self._GadgetError as e:
				failures[e] = gadget
			except:
				logger.debug(f'{gadget!r} failed while trying to produce {gizmo!r}')
				raise
		if failures:
			raise self._AssemblyFailedError(gizmo, failures)
		raise self._GadgetError(gizmo)



class LoopyGaggle(GaggleBase):
	_grabber_stack: dict[str, Iterator[AbstractGadget]] = None

	def __init__(self, *args, grabber_stack: Optional[Mapping] = None, **kwargs):
		if grabber_stack is None:
			grabber_stack = {}
		super().__init__(*args, **kwargs)
		self._grabber_stack = grabber_stack


	def grab_from(self, ctx: 'AbstractGig', gizmo: str) -> Any:
		failures = OrderedDict()
		itr = self._grabber_stack.setdefault(gizmo, self._vendors(gizmo))
		# should be the same as Kit, except the iterators are cached until the gizmo is produced
		for gadget in itr:
			try:
				out = gadget.grab_from(ctx, gizmo)
			except self._GadgetError as e:
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
			raise self._AssemblyFailedError(gizmo, failures)
		raise self._GadgetError(gizmo)



class MutableGaggle(GaggleBase):
	def include(self, *gadgets: AbstractGadget) -> Self:
		'''adds given tools in reverse order'''
		return self.extend(gadgets)


	def extend(self, gadgets: Iterable[AbstractGadget]) -> Self:
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
		'''removes the given tools, if they are found'''
		for gadget in gadgets:
			for gizmo in gadget.gizmos():
				if gizmo in self._gadgets_table and gadget in self._gadgets_table[gizmo]:
					self._gadgets_table[gizmo].remove(gadget)
		return self



class CraftyGaggle(GaggleBase, InheritableCrafty):
	def _process_crafts(self):
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














