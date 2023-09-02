from typing import Optional, Iterator
from itertools import chain
from omnibelt import filter_duplicates

from .abstract import AbstractGadget, AbstractGaggle, AbstractGig
from .errors import GadgetFailed, MissingGizmo
from .tools import ToolCraft, AutoToolCraft, ToolDecorator, AutoToolDecorator
from .gaggles import MutableGaggle, LoopyGaggle, CraftyGaggle
from .gigs import CacheGig



class tool(AutoToolDecorator):
	from_context = ToolDecorator



class ToolKit(LoopyGaggle, MutableGaggle, CraftyGaggle):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._process_crafts()



class Context(CacheGig, LoopyGaggle, MutableGaggle, AbstractGig):
	def __init__(self, *gadgets: AbstractGadget, **kwargs):
		super().__init__(**kwargs)
		self.include(*gadgets)











