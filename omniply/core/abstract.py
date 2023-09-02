from typing import Iterator, Optional, Any
from omnibelt import unspecified_argument



class AbstractGadget:
	def gizmos(self) -> Iterator[str]:
		'''lists known products of this tool'''
		raise NotImplementedError


	def grab_from(self, ctx: Optional['AbstractGig'], gizmo: str) -> Any:
		'''returns the given gizmo from this gadget, or raises ToolFailedError'''
		raise NotImplementedError


	def grabable(self, gizmo: str) -> bool:
		'''returns True if this tool can produce the given gizmo'''
		return gizmo in self.gizmos()


	def __repr__(self):
		return f'{self.__class__.__name__}({", ".join(map(str, self.gizmos()))})'



class AbstractGaggle(AbstractGadget):
	def gadgets(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		'''returns all known gadgets in this gaggle (iterates over leaves)'''
		for gadget in self.vendors(gizmo):
			if isinstance(gadget, AbstractGaggle):
				yield from gadget.gadgets(gizmo)
			else:
				yield gadget


	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		'''returns all known gadgets that can produce the given gizmo (iterates over local branches)'''
		raise NotImplementedError



class AbstractMultiGadget(AbstractGaggle):
	'''a special kind of gaggle that doesn't allow subtools to be accessed directly through vendors()'''
	def gadgets(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		'''yields self, since this is a multi-gadget so it doesn't delegate to subgadgets'''
		yield self


	def vendors(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		'''yields self, since this is a multi-gadget so it doesn't delegate to subgadgets'''
		yield self



class AbstractGig(AbstractMultiGadget):
	'''
	Gigs are a specific type of gadget which takes ownership of a grab_from call,
	rather than (usually silently) delegating to an appropriate gadget.

	That means in general, a gaggle's grab_from method is not called directly, but rather the containing
	gadgets are accessed through the gaggle's vendors method.

	Also, generally gigs are the top-level interface for users.
	'''
	def grab(self, gizmo: str, default: Any = unspecified_argument):
		'''
		convenience function for grab_from to match dict.get api
		returns the given gizmo from this gadget, or raises ToolFailedError
		'''
		try:
			return self.grab_from(None, gizmo)
		except AbstractGadgetFailedError:
			if default is unspecified_argument:
				raise
			return default


	def __getitem__(self, item):
		return self.grab(item)



class AbstractGadgetFailedError(Exception):
	'''base class for all errors raised by gadgets'''
	pass



###########################################################################################



class AbstractGang(AbstractGig):
	'''
	a special kind of gig that relabels gizmos (behaves a bit like a local/internal scope for sub gadgets,
	and defaults to the global/external scope)
	'''
	# def _gizmos(self) -> Iterator[str]:
	# 	'''lists gizmos produced by self (using internal names)'''
	# 	yield from super().gizmos()
	#
	# def gizmos(self) -> Iterator[str]:
	# 	'''lists gizmos produced by self (using external names)'''
	# 	for gizmo in self._gizmos():
	# 		yield self.gizmo_to(gizmo)


	def gizmo_from(self, gizmo: str) -> str: # external -> internal
		'''converts external -> internal gizmo names'''
		raise NotImplementedError


	def gizmo_to(self, gizmo: str) -> str: # internal -> external
		'''converts internal -> external gizmo names'''
		raise NotImplementedError





