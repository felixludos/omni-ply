from typing import Iterable, Callable, Any
from .abstract import AbstractGadget, AbstractGaggle, AbstractGame, AbstractGang
from .errors import GadgetFailed, MissingGadget
from .tools import ToolCraftBase, AutoToolCraft, MIMOToolDecorator, AutoToolDecorator
from .gizmos import DashGizmo
from .gaggles import MutableGaggle, CraftyGaggle, MutableCrafty, LoopyGaggle
from .games import CacheGame, GatedCache, TraceGame, RollingGame, ConsistentGame
from .graces import BacktrackingGaggle, BacktrackingCache, GracefulRepeater, GracefulGaggle, GracefulCache
from .gangs import CachableMechanism, GateBase
from .recording import RecordableGaggle, RecordableMechanism, RecordableCached
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



# class ToolKit(BacktrackingGaggle, MutableGaggle, CraftyGaggle, GeneticGaggle): # TODO: replace loopy with backtracking gaggle
class ToolKit(GracefulGaggle, MutableGaggle, CraftyGaggle, GeneticGaggle): # TODO: replace loopy with backtracking gaggle
	"""
	The ToolKit class is a subclass of LoopyGaggle, MutableGaggle, and CraftyGaggle. It provides methods to handle
	tools in a kit.

	Methods:
		__init__(self, *args, **kwargs): Initializes a new instance of the ToolKit class.
	"""

	def __init__(self, *gadgets: AbstractGadget, **kwargs):
		"""
		Initializes a new instance of the ToolKit class.

		This method initializes the superclass with the provided arguments and processes the crafts in the tool kit.

		Args:
			args: Variable length argument list.
			kwargs: Arbitrary keyword arguments.
		"""
		super().__init__(**kwargs)
		self.extend(gadgets) # note that you can add tools before crafts, but only if they are passed here!
		self._process_crafts()

# class Context(GatedCache, ConsistentGame, RollingGame, LoopyGaggle, MutableGaggle, GeneticGaggle, AbstractGame):
# class Context(GatedCache, ConsistentGame, RollingGame, BacktrackingCache, MutableGaggle, GeneticGaggle, AbstractGame):
# class Context(GatedCache, ConsistentGame, RollingGame, GracefulCache, MutableGaggle, GeneticGaggle, AbstractGame):
class Context(GatedCache, ConsistentGame, RollingGame, RecordableCached, GracefulCache, RecordableGaggle, MutableGaggle, GeneticGaggle, AbstractGame):
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
		self.extend(gadgets)


	def gabel(self, *args, **kwargs):
		'''effectively a shallow copy, excluding the cache'''
		new = self.__class__(*args, **kwargs)
		new.extend(self.vendors())
		return new


	def get(self, key: str, default: Any = None) -> Any:
		return self.grab(key, default=default)


	def __getitem__(self, item):
		"""
		Returns the grabbed item from the context.

		Args:
			item: The item to be grabbed from the context.

		Returns:
			Any: The grabbed item from the context.
		"""
		return self.grab(item)



class Mechanism(RecordableMechanism, MutableGaggle, AbstractGang):
	"""
	The Gang class is a subclass of CachableGang, LoopyGaggle, and MutableGaggle.

	It provides methods to handle gadgets in a gang.
	"""
	def __init__(self, *gadgets: AbstractGadget, **kwargs):
		"""
		Initializes a new instance of the Gang class.

		This method initializes the superclass with the provided arguments and includes the provided gadgets in the gang.

		Args:
			gadgets (AbstractGadget): The gadgets to be included in the gang.
			kwargs: Arbitrary keyword arguments.
		"""
		super().__init__(**kwargs)
		self.extend(gadgets)


	def __getitem__(self, item):
		"""
		Returns the grabbed item from the context.

		Args:
			item: The item to be grabbed from the context.

		Returns:
			Any: The grabbed item from the context.
		"""
		return self.grab(item)



class Gate(Mechanism, GateBase):
	"""
	The Gate class is a subclass of GateBase, CachableGang, LoopyGaggle, and MutableGaggle.

	It provides methods to handle gadgets in a gate, which is a simplified gang.
	"""
	pass