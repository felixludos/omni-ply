from typing import Iterable, Callable
from .abstract import AbstractGadget, AbstractGaggle, AbstractGame, AbstractGate, AbstractGenerous
from .errors import GadgetFailure, MissingGadget
from .tools import ToolCraftBase, AutoToolCraft, MIMOToolDecorator, AutoToolDecorator
from .gizmos import DashGizmo
from .gaggles import MutableGaggle, LoopyGaggle, CraftyGaggle
from .games import CacheGame, GatedCache, TraceGame, RollingGame, ConsistentGame
from .gates import GateBase, CachableGate, SelectiveGate
from .genetics import GeneticGaggle



class tool(AutoToolDecorator):
	"""
	The tool class is a subclass of AutoToolDecorator. It provides a convenient way to create tool instances
	with automatic function gadget capabilities. It does not specify a gizmo type, meaning it can handle any type of gizmo.

	Attributes:
		_gizmo_type (None): The type of the gizmo. Defaults to None.
	"""

	# _gizmo_type = DashGizmo

	class from_context(MIMOToolDecorator):
		"""
		The from_context class is a nested class within tool that inherits from ToolDecorator. It provides a way to create
		tool instances that handle DashGizmo types specifically. This is useful when the gizmos being handled contain dashes.

		Attributes:
			_gizmo_type (DashGizmo): The type of the gizmo. Defaults to DashGizmo.
		"""
		# _gizmo_type = DashGizmo
		def __init__(self, *args, parents: Iterable[str] = None, **kwargs):
			super().__init__(*args, **kwargs)
			self._parents = parents


		def _actualize_tool(self, fn: Callable, **kwargs):
			return super()._actualize_tool(fn, parents=self._parents, **kwargs)



class ToolKit(LoopyGaggle, MutableGaggle, CraftyGaggle, GeneticGaggle):
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


class Context(GatedCache, ConsistentGame, RollingGame, LoopyGaggle, MutableGaggle, GeneticGaggle,
			  AbstractGenerous, AbstractGame):
	"""
	The Context class is a subclass of GateCache, LoopyGaggle, MutableGaggle, and AbstractGame. It provides methods to handle
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


	def gabel(self):
		'''effectively a shallow copy, excluding the cache'''
		return self.__class__(*self._vendors())


	def __getitem__(self, item):
		"""
		Returns the grabbed item from the context.

		Args:
			item: The item to be grabbed from the context.

		Returns:
			Any: The grabbed item from the context.
		"""
		return self.grab(item)


class Scope(CachableGate, LoopyGaggle, MutableGaggle, AbstractGate):
	"""
	The Scope class is a subclass of CachableGate, LoopyGaggle, MutableGaggle, and AbstractGate. It provides methods
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

class Selection(SelectiveGate, Scope):
	"""
	The Selection class is a subclass of SelectiveGate and Scope. It provides methods to handle selective gizmo mapping
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