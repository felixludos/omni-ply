import logging
import yaml
from typing import Optional
from collections import OrderedDict
from .abstract import AbstractGadgetError, AbstractGadget

logger = logging.getLogger('omniply')



class GadgetFailure(AbstractGadgetError):
	'''General error for when a gadget fails to grab a gizmo'''
	def __init__(self, message: Optional[str] = None):
		super().__init__(message)
		self.message = message

	def __hash__(self):
		return hash(repr(self))


	def __eq__(self, other):
		return repr(self) == repr(other)


	@property
	def description(self) -> str:
		return str(self)



class MissingGadget(GadgetFailure, KeyError):
	'''Error for when a gadget fails to grab a gizmo because the gadget can't find it'''
	def __init__(self, gizmo: str, *, message: Optional[str] = None):
		if message is None:
			message = gizmo
		super().__init__(message)
		self.gizmo = gizmo

	@property
	def description(self) -> str:
		return f'missing gadget for {self.gizmo!r}'



class AssemblyError(GadgetFailure):
	'''Error for when a gadget fails to grab a gizmo because the gizmo can't be assembled from the gadgets available'''
	def __init__(self, failures: OrderedDict[GadgetFailure, AbstractGadget], *,
				 message: Optional[str] = None):
		if message is None:
			errors = [str(error) for error in failures]
			message = f'{len(errors)} failures: {", ".join(errors)}'
		super().__init__(message)
		self.failures = failures



class GrabError(AbstractGadgetError):
	def __init__(self, gizmo: str, error: AbstractGadgetError, *, message: Optional[str] = None):
		if message is None:
			message = f'{gizmo!r} failed due to: {error.description}'
		super().__init__(message)
		self.error = error
		self.gizmo = gizmo

	@property
	def description(self) -> str:
		return str(self)



class ApplicationAmbiguityError(ValueError):
	def __init__(self, gizmo: str, options: list[str], *, message: Optional[str] = None):
		if message is None:
			message = f'{gizmo!r} cant choose between: {options}'
		super().__init__(message)
		self.gizmo = gizmo
		self.options = options



