from typing import Iterable, Self, Mapping, Any, Iterator
from collections import UserDict

from .. import AbstractGadget, AbstractGaggle
from ..core.gaggles import CraftyGaggle, MutableGaggle
from ..core.games import CacheGame
from ..core.tools import ToolCraft, AutoToolCraft
from ..core.genetics import AutoMIMOFunctionGadget
from .. import ToolKit as _ToolKit, tool as _tool, Context as _Context

# gauges are not aliases - instead they replace existing gizmos ("relabeling" only, no remapping)

GAUGE = dict[str, str]


class AbstractGauged(AbstractGadget):
	def gauge_apply(self, gauge: GAUGE) -> Self:
		raise NotImplementedError



class AbstractGapped(AbstractGauged):
	def gap(self, internal_gizmo: str) -> str:
		'''Converts an internal gizmo to its external representation.'''
		raise NotImplementedError



class Gauged(AbstractGauged):
	'''Gauges allow you to relabel output gizmos'''
	def __init__(self, *args, gap: Mapping[str, str] = None, **kwargs):
		if gap is None: gap = {}
		super().__init__(*args, **kwargs)
		self._gauge = gap


	def gauge_apply(self, gauge: GAUGE) -> Self:
		'''Applies the gauge to the Gauged.'''
		new = gauge.copy()
		for gizmo, gap in self._gauge.items():
			if gap in gauge:
				self._gauge[gizmo] = new.pop(gap)
		self._gauge.update(new)
		return self



class Gapped(Gauged, AbstractGapped):
	'''Gapped gauges allow you to relabel inputs as well'''
	def gap(self, internal_gizmo: str) -> str:
		'''Converts an internal gizmo to its external representation. Meant only for inputs to this gadget.'''
		return self._gauge.get(internal_gizmo, internal_gizmo)



# class GappedCap(Gapped):
# 	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
# 		return super().grab_from(ctx, self.gap(gizmo))



class GaugedGaggle(MutableGaggle, Gauged):
	# don't regauge new gadgets when they are added (gauges are stateless)
	# def extend(self, gadgets: Iterable[AbstractGauged]) -> Self:
	# 	'''Extends the Gauged with the provided gadgets.'''
	# 	gadgets = list(gadgets)
	# 	for gadget in gadgets:
	# 		# if isinstance(gadget, AbstractGauged):
	# 		gadget.gauge_apply(self._gauge)
	# 	return super().extend(gadgets)


	def gauge_apply(self, gauge: GAUGE) -> Self:
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
	def gauge_apply(self, gauge: GAUGE) -> Self:
		super().gauge_apply(gauge)
		cached = {key: value for key, value in self.data.items() if key in gauge}
		for key, value in cached.items():
			del self.data[key]
		self.data.update({gauge[key]: value for key, value in cached.items()})
		return self



class AutoFunctionGapped(AutoMIMOFunctionGadget, AbstractGapped):
	def gap(self, internal_gizmo: str) -> str:
		'''Converts an internal gizmo to its external representation.'''
		return self._arg_map.get(internal_gizmo, internal_gizmo)


	def gauge_apply(self, gauge: GAUGE) -> Self:
		'''Applies the gauge to the Gauged.'''
		new = gauge.copy()
		for gizmo, gap in self._arg_map.items():
			if gap in gauge:
				self._arg_map[gizmo] = new.pop(gap)
		self._arg_map.update(new)
		return self


	def gizmos(self) -> Iterator[str]:
		for gizmo in super().gizmos():
			yield self.gap(gizmo)



class GappedTool(ToolCraft):
	class _ToolSkill(Gapped, ToolCraft._ToolSkill):
		def gizmos(self) -> Iterable[str]:
			'''Lists the gizmos produced by the tool.'''
			for gizmo in super().gizmos():
				yield self.gap(gizmo)



class GappedAutoTool(AutoFunctionGapped, AutoToolCraft):
	class _ToolSkill(AutoFunctionGapped, AutoToolCraft._ToolSkill):
		pass



class ToolKit(_ToolKit, Gapped, GaugedGaggle):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.gauge_apply(self._gauge)



class Context(_Context, GaugedGame):
	pass



class tool(_tool):
	_ToolCraft = GappedAutoTool
	class from_context(_tool.from_context):
		_ToolCraft = GappedTool


from .simple import DictGadget as _DictGadget, Table as _Table


class DictGadget(Gauged, _DictGadget): # TODO: unit test this and the GappedCap
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.gauge_apply(self._gauge)

	def gauge_apply(self, gauge: GAUGE) -> Self:
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

	def gauge_apply(self, gauge: GAUGE) -> Self:
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












