import logging
from typing import Optional
from collections import OrderedDict
from .abstract import AbstractGadgetFailedError, AbstractGadget

logger = logging.getLogger('omniply')



class GadgetError(AbstractGadgetFailedError):
	'''General error for when a gadget fails to grab a gizmo'''
	def __init__(self, gizmo: str, *, message: Optional[str] = None):
		if message is None:
			message = f'{gizmo!r}'
		super().__init__(message)
		self.gizmo = gizmo


	def __hash__(self):
		return hash(repr(self))


	def __eq__(self, other):
		return repr(self) == repr(other)



class GadgetFailure(GadgetError):
	'''Error for when a gadget fails to grab a gizmo'''
	def __init__(self, message: str, gizmo: Optional[str] = None):
		super().__init__(gizmo, message=message)



class MissingGizmo(GadgetError, KeyError):
	'''Error for when a gadget fails to grab a gizmo because the gadget can't find it'''
	def __init__(self, gizmo: str, *, message: Optional[str] = None):
		if message is None:
			message = gizmo
		super().__init__(gizmo, message=message)



class AssemblyError(GadgetError):
	'''Error for when a gadget fails to grab a gizmo because the gizmo can't be assembled from the gadgets available'''
	def __init__(self, gizmo: str, failures: OrderedDict[GadgetError, AbstractGadget], *,
				 message: Optional[str] = None):
		if message is None:
			message = f'{gizmo!r} due to {failures}'
		super().__init__(gizmo, message=message)
		self.failures = failures



class GigError(GadgetError):
	def __init__(self, gizmo: str, error: GadgetError, *, message: Optional[str] = None):
		if message is None:
			message = f'{gizmo!r} due to {error!r}'
		super().__init__(gizmo, message=message)
		self.error = error



class ApplicationAmbiguityError(ValueError):
	def __init__(self, gizmo: str, options: list[str], *, message: Optional[str] = None):
		if message is None:
			message = f'{gizmo!r} cant choose between: {options}'
		super().__init__(message)
		self.gizmo = gizmo
		self.options = options



