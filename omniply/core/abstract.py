from typing import Iterator, Optional, Any, Union
from omnibelt import unspecified_argument



class AbstractGizmo:
	"""
	AbstractGizmo is an abstract base class for custom labels of gizmos.

	Gizmos are the basic unit of data in `omni-ply`. They are used to represent both the input and output
	of gadgets. While the data itself may have any type, the label is by default a string, however if you would like
	to use a custom type of label, you can subclass AbstractGizmo and use that instead.
	"""

	def __new__(cls, label: Union[str, 'AbstractGizmo']):
		"""
		Constructor method for the AbstractGizmo class. It checks if the label is an instance of
		AbstractGizmo. If it is, it returns the label itself. Otherwise, it creates a new instance of the class.

		Args:
			label (Union[str, 'AbstractGizmo']): A string or an instance of AbstractGizmo.

		Returns:
			An instance of AbstractGizmo.
		"""
		if isinstance(label, AbstractGizmo):
			return label
		return super().__new__(cls)

	def __eq__(self, other) -> bool:
		"""
		Checks if the current instance is equal to another object. It does this by comparing
		their string representations.

		Args:
			other: The object to compare with.

		Returns:
			bool: True if the objects are equal, False otherwise.
		"""
		return str(self) == str(other)

	def __hash__(self) -> int:
		"""
		Returns the hash of the string representation of the current instance.

		Returns:
			int: The hash of the string representation of the current instance.
		"""
		return hash(str(self))


class AbstractGadgetError(Exception):
	"""
	AbstractGadgetError is an abstract base class for all exceptions that are raised by gadgets that should be
	handled by the inference engine.

	This class must be subclassed to create more specific exceptions raised by gadgets (see `errors.py`).
	"""

	@property
	def description(self) -> str:
		"""
		Returns a string description of the error. This method should be overridden by subclasses to provide the actual implementation.

		Returns:
			str: A string description of the error.
		"""
		raise NotImplementedError


class AbstractGadget:
	"""
	Gadgets define transformations of gizmos in `omni-ply`, and are the primary workhorses of the framework.
	Pretty much any class or function that you would like to use with the `omni-ply` structure, will be in the form
	of a subclass of this.

	AbstractGadget is an abstract base class for any custom gadget types.
	"""

	def gizmos(self) -> Iterator[str]:
		"""
		Generates all known products of this gadget.

		This method must be overridden by subclasses to provide the actual implementation.

		Returns:
			Iterator[str]: An iterator over the known products of this tool.
		"""
		raise NotImplementedError

	def grab_from(self, ctx: 'AbstractGig', gizmo: str) -> Any:
		"""
		Transforms the given context `ctx` to produce the specified `gizmo`, or raises ToolFailedError.
		The context can be expected to contain all the necessary input gizmos.

		This method should be overridden by subclasses to provide the actual implementation.

		Args:
			ctx (Optional['AbstractGig']): The context from which to grab any necessary input gizmos.
			gizmo (str): The gizmo that must be produced.

		Returns:
			Any: The specified output gizmo.

		Raises:
			ToolFailedError: If the gizmo cannot be grabbed (possibly because a necessary input gizmo is missing).
		"""
		raise NotImplementedError

	def grabable(self, gizmo: str) -> bool:
		"""
		Checks if this tool can produce the given gizmo.

		Args:
			gizmo (str): The gizmo to check.

		Returns:
			bool: True if this tool can produce the given gizmo, False otherwise.
		"""
		return gizmo in self.gizmos()

	def __repr__(self) -> str:
		"""
		Returns a string representation of this gadget.

		Returns:
			str: A string representation of this gadget.
		"""
		return f'{self.__class__.__name__}({", ".join(map(str, self.gizmos()))})'


class AbstractGaggle(AbstractGadget):
	"""
	A gaggle is a collection of gadgets, which because similar to a gadget, except that it can access sub-gadgets
	to produce specific gizmos.

	It provides methods to list all known gadgets and to return all known gadgets that can produce a given gizmo.
	This class is typically subclassed to create a custom types of gaggles.
	"""

	def gadgets(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		"""
		Lists all known gadgets under this gaggle in order of precedence.. If a gizmo is specified, it iterates over
		the gadgets that can produce the given gizmo. Note that, this will recursively iterate through all sub-gaggles
		and only yield the gadgets (ie. leaves of the tree).

		Args:
			gizmo (Optional[str]): If specified, yields only the gadgets that can produce this gizmo.

		Returns:
			Iterator[AbstractGadget]: An iterator over the known gadgets in this gaggle that can produce the
			specified gizmo.
		"""
		for gadget in self.vendors(gizmo):
			if isinstance(gadget, AbstractGaggle):
				yield from gadget.gadgets(gizmo)
			else:
				yield gadget

	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		"""
		Lists all known sub-gadgets and sub-gaggles in this gaggle in order of precedence.

		Unlike `gadgets()`, this does not recursively iterate through sub-gaggles. It only considers the gadgets
		that are directly contained in this gaggle.

		This method must be overridden by subclasses to provide the actual implementation.

		Args:
			gizmo (Optional[str]): If specified, yields only the gadgets that can produce this gizmo.

		Returns:
			Iterator[AbstractGadget]: An iterator over the known gadgets that can directly produce the given gizmo.
		"""
		raise NotImplementedError


class AbstractMultiGadget(AbstractGaggle):
	"""
	AbstractMultiGadget is a special kind of gaggle that hides all sub-gadgets from being accessed through `gadgets()`
	and `vendors()`. Instead, it presents itself as a gadget that can produce all the products of the sub-gadgets.

	Generally, if you know before runtime what gizmos a gadget can produce, then it should just be a gadget, however,
	if you want to be able to dynamically add sub-gadgets, while still preventing delegation, then you can use this.

	"""

	def gadgets(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		"""
		Lists all known gadgets under this multi-gadget that can produce the given gizmo.
		Since this is a multi-gadget, it doesn't delegate to sub-gadgets, and instead yields itself.

		Args:
			gizmo (Optional[str]): If specified, yields only the gadgets that can produce this gizmo. In this case, it
			has no effect.

		Returns:
			Iterator[AbstractGadget]: An iterator over the known gadgets in this multi-gadget that can produce the
			specified gizmo. Since this is a multi-gadget, it yields only itself.
		"""
		yield self

	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		"""
		Lists all known sub-gadgets and sub-gaggles in this multi-gadget that can produce the given gizmo.
		Since this is a multi-gadget, it doesn't delegate to sub-gadgets, and instead yields itself.

		Args:
			gizmo (Optional[str]): If specified, yields only the gadgets that can produce this gizmo. In this case, it
			checks if this multi-gadget can produce the gizmo.

		Returns:
			Iterator[AbstractGadget]: An iterator over the known gadgets that can directly produce the given gizmo. Since
			this is a multi-gadget, it yields itself.
		"""
		yield self


_unique_gig_default_value = object()


class AbstractGig(AbstractMultiGadget):
	"""
	Gigs are usually the top-level interface for users to use the inference engine of `omni-ply`. Gigs are a special
	kind of gaggle that takes ownership of a `grab_from()` call, rather than (usually silently) delegating to an
	appropriate gadget to produce the specified gizmo. This also means gigs are responsible providing the current
	context for gadgets (which often includes caching existing gizmos).
	"""

	def grab(self, gizmo: str, default: Any = _unique_gig_default_value):
		"""
		Convenience function for grab_from to match dict.get API. It returns the given gizmo from this gadget,
		or raises ToolFailedError if the gizmo cannot be grabbed and no default value is provided.

		Args:
			gizmo (str): The gizmo to grab.
			default (Any): The default value to return if the gizmo cannot be grabbed. If not specified,
			ToolFailedError is raised when the gizmo cannot be grabbed.

		Returns:
			Any: The grabbed gizmo, or the default value if the gizmo cannot be grabbed and a default value is provided.

		Raises:
			AbstractGadgetError: If the gizmo cannot be grabbed and no default value is provided.
		"""
		try:
			return self.grab_from(None, gizmo)
		except AbstractGadgetError:
			if default is _unique_gig_default_value:
				raise
			return default


class AbstractGang(AbstractGig):
	"""
	Gangs are a special kind of gig that relabels gizmos. It behaves a bit like a local/internal scope
	for its sub-gadgets, and can default to the global/external scope if necessary.

	This class must be typically subclassed to create a specific type of gang.
	"""

	def gizmo_from(self, gizmo: str) -> str:
		"""
		Converts external gizmo names to internal gizmo names used by sub-gadgets.

		This method must be overridden by subclasses to provide the actual implementation.

		Args:
			gizmo (str): The external gizmo name to convert.

		Returns:
			str: The internal gizmo name.
		"""
		raise NotImplementedError

	def gizmo_to(self, gizmo: str) -> str:
		"""
		Converts internal gizmo names used by sub-gadgets to external gizmo names.

		This method must be overridden by subclasses to provide the actual implementation.

		Args:
			gizmo (str): The internal gizmo name to convert.

		Returns:
			str: The external gizmo name.
		"""
		raise NotImplementedError



# Moguls -> Guru

