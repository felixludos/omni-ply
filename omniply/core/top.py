from .abstract import AbstractGadget, AbstractGaggle, AbstractGig, AbstractGang
from .errors import GadgetFailure, MissingGadget
from .tools import ToolCraft, AutoToolCraft, ToolDecorator, AutoToolDecorator
from .gizmos import DashGizmo
from .gaggles import MutableGaggle, LoopyGaggle, CraftyGaggle
from .gigs import CacheGig, GroupCache
from .groups import GroupBase, CachableGroup, SelectiveGroup



class tool(AutoToolDecorator):
	"""
	The tool class is a subclass of AutoToolDecorator. It provides a convenient way to create tool instances
	with automatic function gadget capabilities. It does not specify a gizmo type, meaning it can handle any type of gizmo.

	Attributes:
		_gizmo_type (None): The type of the gizmo. Defaults to None.
	"""

	# _gizmo_type = DashGizmo

	class from_context(ToolDecorator):
		"""
		The from_context class is a nested class within tool that inherits from ToolDecorator. It provides a way to create
		tool instances that handle DashGizmo types specifically. This is useful when the gizmos being handled contain dashes.

		Attributes:
			_gizmo_type (DashGizmo): The type of the gizmo. Defaults to DashGizmo.
		"""
		# _gizmo_type = DashGizmo
		pass


class ToolKit(LoopyGaggle, MutableGaggle, CraftyGaggle):
	"""
	The ToolKit class is a subclass of LoopyGaggle, MutableGaggle, and CraftyGaggle. It provides methods to handle
	tools in a kit.

	Methods:
		__init__(self, *args, **kwargs): Initializes a new instance of the ToolKit class.
	"""

	def __init__(self, *args, **kwargs):
		"""
		Initializes a new instance of the ToolKit class.

		This method initializes the superclass with the provided arguments and processes the crafts in the tool kit.

		Args:
			args: Variable length argument list.
			kwargs: Arbitrary keyword arguments.
		"""
		super().__init__(*args, **kwargs)
		self._process_crafts()


class Context(GroupCache, LoopyGaggle, MutableGaggle, AbstractGig):
	"""
	The Context class is a subclass of GroupCache, LoopyGaggle, MutableGaggle, and AbstractGig. It provides methods to handle
	gadgets in a context.

	Methods:
		__init__(self, *gadgets: AbstractGadget, **kwargs): Initializes a new instance of the Context class.
		__getitem__(self, item): Returns the grabbed item from the context.
	"""

	# _gizmo_type = DashGizmo # TODO

	def __init__(self, *gadgets: AbstractGadget, **kwargs):
		"""
		Initializes a new instance of the Context class.

		This method initializes the superclass with the provided arguments and includes the provided gadgets in the context.

		Args:
			gadgets (AbstractGadget): The gadgets to be included in the context.
			kwargs: Arbitrary keyword arguments.
		"""
		super().__init__(**kwargs)
		self.include(*gadgets)

	def __getitem__(self, item):
		"""
		Returns the grabbed item from the context.

		Args:
			item: The item to be grabbed from the context.

		Returns:
			Any: The grabbed item from the context.
		"""
		return self.grab(item)


class Scope(CachableGroup, LoopyGaggle, MutableGaggle, AbstractGang):
	"""
	The Scope class is a subclass of CachableGroup, LoopyGaggle, MutableGaggle, and AbstractGang. It provides methods
	to handle gadgets in a scope.

	Methods:
		__init__(self, *gadgets: AbstractGadget, **kwargs): Initializes a new instance of the Scope class.
	"""

	def __init__(self, *gadgets: AbstractGadget, **kwargs):
		"""
		Initializes a new instance of the Scope class.

		This method initializes the superclass with the provided arguments and includes the provided gadgets in the scope.

		Args:
			gadgets (AbstractGadget): The gadgets to be included in the scope.
			kwargs: Arbitrary keyword arguments.
		"""
		super().__init__(**kwargs)
		self.include(*gadgets)

	def __getitem__(self, item):
		"""
		Returns the grabbed item from the context.

		Args:
			item: The item to be grabbed from the context.

		Returns:
			Any: The grabbed item from the context.
		"""
		return self.grab(item)

class Selection(SelectiveGroup, Scope):
	"""
	The Selection class is a subclass of SelectiveGroup and Scope. It provides methods to handle selective gizmo mapping
	within a scope.

	Methods:
		__init__(self, *gadgets: AbstractGadget, **kwargs): Initializes a new instance of the Selection class.
	"""

	def __init__(self, *gadgets: AbstractGadget, **kwargs):
		"""
		Initializes a new instance of the Selection class.

		This method initializes the superclass with the provided arguments and includes the provided gadgets in the selection.

		Args:
			gadgets (AbstractGadget): The gadgets to be included in the selection.
			kwargs: Arbitrary keyword arguments.
		"""
		super().__init__(*gadgets, **kwargs)

	def __getitem__(self, item):
		"""
		Returns the grabbed item from the context.

		Args:
			item: The item to be grabbed from the context.

		Returns:
			Any: The grabbed item from the context.
		"""
		return self.grab(item)