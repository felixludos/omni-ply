from typing import Iterable, Mapping, Any, Iterator, TypeVar
from collections import UserDict

from .. import AbstractGadget, AbstractGaggle
from ..core.gaggles import CraftyGaggle, MutableGaggle
from ..core.games import CacheGame
from ..core.tools import ToolCraft, AutoToolCraft
from ..core.genetics import AutoMIMOFunctionGadget, AutoFunctionGadget
from .. import ToolKit as _ToolKit, tool as _tool, Context as _Context, gear as _gear, Mechanics as _Mechanics
from ..gears.gears import GearCraft, AutoGearCraft, GearSkill
from ..gears.gearbox import GearedGaggle, GearBox as _GearBox
from ..gears.mechanics import MechanizedBase

# gauges are not aliases - instead they replace existing gizmos ("relabeling" only, no remapping)

Self = TypeVar('Self')

GAUGE = dict[str, str]


class AbstractGauged(AbstractGadget):
	def gauge_apply(self: Self, gauge: GAUGE) -> Self:
		raise NotImplementedError



class AbstractGapped(AbstractGauged):
	def gap(self, internal_gizmo: str) -> str:
		'''Converts an internal gizmo to its external representation.'''
		raise NotImplementedError


	def gap_invert(self, external_gizmo: str) -> str:
		'''Converts an external gizmo to its internal representation (only when its unambiguous).'''
		raise NotImplementedError



class Gauged(AbstractGauged):
	'''Gauges allow you to relabel output gizmos'''
	def __init__(self, *args, gap: Mapping[str, str] = None, **kwargs):
		'''gap: internal gizmo -> external gizmo'''
		if gap is None: gap = {}
		super().__init__(*args, **kwargs)
		self._gauge = gap


	def gauge_apply(self: Self, gauge: GAUGE) -> Self:
		'''Applies the gauge to the Gauged.'''
		new = gauge.copy()
		for gizmo, gap in self._gauge.items():
			if gap in gauge:
				self._gauge[gizmo] = new.pop(gap)
		self._gauge.update(new)
		return self



class GappedGadget(AbstractGapped):
	def gizmos(self) -> Iterator[str]:
		for gizmo in super().gizmos():
			yield self.gap(gizmo)



class Gapped(Gauged, GappedGadget):
	'''Gapped gauges allow you to relabel inputs as well'''
	def gap(self, internal_gizmo: str) -> str:
		'''Converts an internal gizmo to its external representation. Meant only for inputs to this gadget.'''
		return self._gauge.get(internal_gizmo, internal_gizmo)

	def gap_invert(self, external_gizmo: str) -> str:
		inv = {}
		for k, v in self._gauge.items():
			inv.setdefault(v, []).append(k)
		if external_gizmo in inv and len(inv[external_gizmo]) == 1:
			return inv[external_gizmo][0]



class GaugedGaggle(MutableGaggle, Gauged):
	def gauge_apply(self: Self, gauge: GAUGE) -> Self:
		'''Applies the gauge to the GaugedGaggle.'''
		super().gauge_apply(gauge)
		for gadget in self.vendors():
			if isinstance(gadget, AbstractGauged):
				gadget.gauge_apply(gauge)
		table = {gauge.get(gizmo, gizmo): gadgets for gizmo, gadgets in self._gadgets_table.items()}
		self._gadgets_table.clear()
		self._gadgets_table.update(table)
		return self



class GaugedGame(CacheGame, GaugedGaggle):
	def gauge_apply(self: Self, gauge: GAUGE) -> Self:
		super().gauge_apply(gauge)
		cached = {key: value for key, value in self.data.items() if key in gauge}
		for key, value in cached.items():
			del self.data[key]
		self.data.update({gauge[key]: value for key, value in cached.items()})
		return self



class AutoFunctionGapped(GappedGadget, AutoFunctionGadget):
	def gap(self, internal_gizmo: str) -> str:
		'''Converts an internal gizmo to its external representation.'''
		return self._arg_map.get(internal_gizmo, internal_gizmo)


	def gap_invert(self, external_gizmo: str) -> str:
		inv = {}
		for k, v in self._arg_map.items():
			inv.setdefault(v, []).append(k)
		if external_gizmo in inv and len(inv[external_gizmo]) == 1:
			return inv[external_gizmo][0]


	def gauge_apply(self, gauge: GAUGE) -> Self:
		'''Applies the gauge to the Gauged.'''
		new = gauge.copy()
		for gizmo, gap in self._arg_map.items():
			if gap in gauge:
				self._arg_map[gizmo] = new.pop(gap)
		self._arg_map.update(new)
		return self



class GearBox(Gapped, _GearBox, GaugedGaggle):
	pass



class GaugedGearedGaggle(GearedGaggle, Gauged):
	_GearBox = GearBox
	# def gearbox(self) -> 'AbstractGearbox':
	# 	gearbox = super().gearbox()
	# 	gearbox.gauge_apply(self._gauge)
	# 	return gearbox
	# 	raise NotImplementedError # apply gauge here (and only here)


	def gearbox(self) -> 'AbstractGearbox':
		return super().gearbox().gauge_apply(self._gauge)



class GaugedMechanized(MechanizedBase, Gauged):
	def gauge_apply(self: Self, gauge: GAUGE) -> Self:
		if self._mechanics is not None:
			self._mechanics.gauge_apply(gauge)
		return super().gauge_apply(gauge)



class GappedTool(Gapped, ToolCraft):
	class _ToolSkill(Gapped, ToolCraft._ToolSkill):
		pass



class GappedAutoTool(AutoFunctionGapped, AutoToolCraft):
	class _ToolSkill(AutoFunctionGapped, AutoToolCraft._ToolSkill):
		pass



class Mechanics(_Mechanics, GaugedGame):
	pass



class ToolKit(_ToolKit, Gapped, GaugedMechanized, GaugedGearedGaggle, GaugedGaggle):
	_Mechanics = Mechanics

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.gauge_apply(self._gauge)



class CarefulGearCraft(GearCraft):
	'''recovers the corresponding skill to apply the correct gap'''

	def __get__(self, instance: ToolKit, owner):
		ctx = self._find_context(instance)
		gizmo = instance.gap(self._gizmo)
		return ctx.grab(gizmo)



class Context(_Context, GaugedGame):
	_Mechanics = Mechanics



class tool(_tool):
	_ToolCraft = GappedAutoTool
	class from_context(_tool.from_context):
		_ToolCraft = GappedTool



class gear(AutoFunctionGapped, CarefulGearCraft, _gear):
	class _GearSkill(AutoFunctionGapped, _gear._GearSkill):
		pass
	# class from_context(Gapped, _gear.from_context):
	# 	class _GearSkill(Gapped, _gear._GearSkill):
	# 		pass




from .simple import DictGadget as _DictGadget, Table as _Table



class DictGadget(Gauged, _DictGadget): # TODO: unit test this and the GappedCap
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.gauge_apply(self._gauge)

	def gauge_apply(self: Self, gauge: GAUGE) -> Self:
		super().gauge_apply(gauge)
		for src in [self.data, *self._srcs]:
			for key in list(src.keys()):
				fix = gauge.get(key, key)
				if fix != key:
					src[fix] = src[key]
					del src[key]
		return self



class Table(Gapped, _Table): # TODO: unit test this
	def load(self):
		trigger = not self.is_loaded
		super().load()
		if trigger:
			self.gauge_apply(self._gauge)
		return self

	def gauge_apply(self: Self, gauge: GAUGE) -> Self:
		super().gauge_apply(gauge)
		if self._index_gizmo is not None and self._index_gizmo in gauge:
			self._index_gizmo = gauge[self._index_gizmo]
		if self.is_loaded:
			for key in list(self.data.keys()):
				fix = gauge.get(key, key)
				if fix != key:
					self.data[fix] = self.data[key]
					del self.data[key]
		return self












