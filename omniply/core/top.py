from .abstract import AbstractGadget, AbstractGaggle, AbstractGig, AbstractGroup
from .errors import GadgetError, MissingGizmo
from .tools import ToolCraft, AutoToolCraft, ToolDecorator, AutoToolDecorator
from .gaggles import MutableGaggle, LoopyGaggle, CraftyGaggle
from .gigs import CacheGig
from .groups import GroupBase


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



class Scope(GroupBase, LoopyGaggle, MutableGaggle, AbstractGroup):
	def __init__(self, *gadgets: AbstractGadget, **kwargs):
		super().__init__(**kwargs)
		self.include(*gadgets)


