from .imports import *
from .abstract import AbstractGeologist, AbstractGeode, AbstractGem
from ..core.gaggles import CraftyGaggle
from omnibelt.crafts import InheritableCrafty, AbstractSkill


class GeologistBase(CraftyGaggle, AbstractGeologist):
	# TODO: switch to subclassing `InheritableCrafty` only
	_gem_list: list[AbstractGem]









