from .imports import *
import inspect
from omnibelt import AbstractStaged, Staged
from .abstract import AbstractGeologist, AbstractGeode, AbstractGem
from ..core.gaggles import CraftyGaggle, MutableGaggle
# from omnibelt.crafts import InheritableCrafty, AbstractSkill



class GemlogistBase(CraftyGaggle, AbstractGeologist):
	# TODO: switch to subclassing `InheritableCrafty` only
	_gems: Iterable[str]
	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		gems = []
		for current, key, craft in cls._emit_all_craft_items():
			if isinstance(craft, AbstractGem) and (current == cls or getattr(craft, 'inherit', False)):
				gems.append(key)
		cls._gems = tuple(gems)

	def _get_gem(self, key: str) -> AbstractGem:
		return inspect.getattr_static(self, key)

	# def __init__(self, *args, **kwargs):
	# 	super().__init__(*args, **kwargs)
	# 	self._process_gems()

	def _process_gems(self):
		for key in self._gems:
			gem = self._get_gem(key)
			if gem is not None:
				gem.reconstruct(self)
	


class EagerGeologist(GemlogistBase):
	def __init__(self, *args, **kwargs):
		values, remaining = self._filter_gems(kwargs)
		super().__init__(*args, **remaining)
		self._process_gems(values)

	def _process_gems(self, values: dict[str, Any] = None):
		super()._process_gems()
		for key in self._gems:
			gem = self._get_gem(key)
			if key in values:
				setattr(self, key, values[key])
			else:
				gem.revitalize(self)

	def _filter_gems(self, kwargs: dict[str, Any]) -> Tuple[dict[str, Any], dict[str, Any]]:
		values, remaining = {}, {}
		for key, value in kwargs.items():
			(values if key in self._gems else remaining)[key] = value
		return values, remaining


class GeologistBase(MutableGaggle, EagerGeologist, Staged):
	_geode_gadgets: dict[str, Tuple[AbstractGadget, ...]]

	def _process_gems(self, values: dict[str, Any] = None):
		if getattr(self, '_geode_gadgets', None) is None:
			self._geode_gadgets = {}
		super()._process_gems(values)
		self.refresh_geodes()

	def refresh_geodes(self, *names: str):
		if len(names) == 0:
			names = self._gems
		for key in names:
			for gadget in self._geode_gadgets.pop(key, []):
				self.exclude(gadget)
			gem = self._get_gem(key)
			if isinstance(gem, AbstractGeode):
				self._geode_gadgets[key] = tuple(gem.relink(self))
				if len(self._geode_gadgets[key]):
					self.extend(self._geode_gadgets[key])


	def _stage(self, scape: Mapping[str, Any] = None) -> Optional[AbstractGeode]:
		"""
		Stages the geologist, returning a geode if applicable.
		"""
		for key in self._gems:
			gem = self._get_gem(key)
			if isinstance(gem, AbstractGeode):
				gem.restage(self, scape)
		return super()._stage(scape)


# TODO: simple decorator to explicitly define what gems should be inherited
