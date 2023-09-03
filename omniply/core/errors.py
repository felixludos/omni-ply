import logging
from typing import Optional
from collections import OrderedDict
from .abstract import AbstractGadgetFailedError, AbstractGadget

logger = logging.getLogger('omniply')



class GadgetFailed(AbstractGadgetFailedError):
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



class MissingGizmo(GadgetFailed, KeyError):
	'''Error for when a gadget fails to grab a gizmo because the gadget can't find it'''
	def __init__(self, gizmo: str, *, message: Optional[str] = None):
		if message is None:
			message = gizmo
		super().__init__(gizmo, message=message)



class AssemblyFailed(GadgetFailed):
	'''Error for when a gadget fails to grab a gizmo because the gizmo can't be assembled from the gadgets available'''
	def __init__(self, gizmo: str, failures: OrderedDict[GadgetFailed, AbstractGadget], *,
				 message: Optional[str] = None):
		if message is None:
			message = f'{gizmo!r} due to {failures}'
		super().__init__(gizmo, message=message)
		self.failures = failures



class GigFailed(GadgetFailed):
	def __init__(self, gizmo: str, error: GadgetFailed, *, message: Optional[str] = None):
		if message is None:
			message = f'{gizmo!r} due to {error!r}'
		super().__init__(gizmo, message=message)
		self.error = error



