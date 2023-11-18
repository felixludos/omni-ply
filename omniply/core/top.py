from .abstract import AbstractGadget, AbstractGaggle, AbstractGig, AbstractGroup
from .errors import GadgetFailure, MissingGadget
from .tools import ToolCraft, AutoToolCraft, ToolDecorator, AutoToolDecorator
from .gizmos import DashGizmo
from .gaggles import MutableGaggle, LoopyGaggle, CraftyGaggle
from .gigs import CacheGig, GroupCache
from .groups import GroupBase, CachableGroup, SelectiveGroup



class tool(AutoToolDecorator):
	# _gizmo_type = DashGizmo
	class from_context(ToolDecorator):
		_gizmo_type = DashGizmo



class ToolKit(LoopyGaggle, MutableGaggle, CraftyGaggle):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._process_crafts()



class Context(GroupCache, LoopyGaggle, MutableGaggle, AbstractGig):
	# _gizmo_type = DashGizmo # TODO
	def __init__(self, *gadgets: AbstractGadget, **kwargs):
		super().__init__(**kwargs)
		self.include(*gadgets)



class Scope(CachableGroup, LoopyGaggle, MutableGaggle, AbstractGroup):
	def __init__(self, *gadgets: AbstractGadget, **kwargs):
		super().__init__(**kwargs)
		self.include(*gadgets)



class Selection(SelectiveGroup, Scope):
	def __init__(self, *gadgets: AbstractGadget, **kwargs):
		super().__init__(*gadgets, **kwargs)


