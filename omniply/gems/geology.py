from .imports import *
from .abstract import AbstractGeologist, AbstractGeode, AbstractGem
from ..core.gaggles import CraftyGaggle
# from omnibelt.crafts import InheritableCrafty, AbstractSkill



class GeologistBase(CraftyGaggle, AbstractGeologist):
	# TODO: switch to subclassing `InheritableCrafty` only
	_gems: Iterable[str]
	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		gems = []
		for current, key, craft in cls._emit_all_craft_items():
			if isinstance(craft, AbstractGem) and (current == cls or craft.inherit):
				gems.append(key)
		cls._gems = tuple(gems)


	def __init__(self, *args, **kwargs):
		values, remaining = self._filter_gems(kwargs)
		super().__init__(*args, **remaining)
		for key, value in values.items():
			setattr(self, key, value)


	def _filter_gems(self, kwargs: dict[str, Any]):
		values, remaining = {}, {}
		for key, value in kwargs.items():
			(values if key in self._gems else remaining)[key] = value
		return values, remaining








