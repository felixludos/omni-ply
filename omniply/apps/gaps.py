from typing import Iterable, Self, Mapping
from collections import UserDict

from .. import AbstractGadget, AbstractGaggle
from ..core.gaggles import CraftyGaggle, MutableGaggle


GAUGE = dict[str, str]


class AbstractGauged(AbstractGadget):
	def gauge_apply(self, gauge: GAUGE) -> Self:
		raise NotImplementedError



class AbstractGapped(AbstractGauged):
	def gap(self, internal_gizmo: str) -> str:
		'''Converts an internal gizmo to its external representation.'''
		raise NotImplementedError



class Gauged(AbstractGauged):
	def __init__(self, *, gauge: Mapping[str, str] = None, **kwargs):
		if gauge is None:
			gauge = {}
		super().__init__(**kwargs)
		self._gauge = gauge


	def gauge_apply(self, gauge: GAUGE) -> Self:
		'''Applies the gauge to the Gauged.'''
		self._gauge.update(gauge)
		return self



class Gapped(AbstractGapped, Gauged):
	def gap(self, internal_gizmo: str) -> str:
		'''Converts an internal gizmo to its external representation.'''
		return self._gauge.get(internal_gizmo, internal_gizmo)



class GaugedGaggle(MutableGaggle, Gauged):
	def extend(self, gadgets: Iterable[AbstractGadget]) -> Self:
		'''Extends the Gauged with the provided gadgets.'''
		gadgets = list(gadgets)
		for gadget in gadgets:
			if isinstance(gadget, AbstractGauged):
				gadget.gauge_apply(self._gauge)
		return super().extend(gadgets)


	def gauge_apply(self, gauge: GAUGE) -> Self:
		'''Applies the gauge to the GaugedGaggle.'''
		super().gauge_apply(gauge)
		for gadget in self.vendors():
			if isinstance(gadget, AbstractGauged):
				gadget.gauge_apply(gauge)
		return self


from ..core.tools import ToolCraft, MIMOGadgetBase
from ..core.gadgets import AutoFunctionGadget


class GappedSkill(AutoFunctionGadget, AbstractGapped):
	def gap(self, internal_gizmo: str) -> str:
		'''Converts an internal gizmo to its external representation.'''
		return self._arg_map.get(internal_gizmo, internal_gizmo)




	pass



from .. import ToolKit as ToolKitBase, tool as tool_base



class ToolKit(ToolKitBase, Gapped, GaugedGaggle):
	pass



class tool(tool_base):
	class from_context(tool_base.from_context, Gapped):



		pass






