from typing import Optional
from .abstract import AbstractGadgetFailedError


class GadgetFailed(AbstractGadgetFailedError):
	'''General error for when a gadget fails to grab a gizmo'''
	def __init__(self, gizmo: str, *, message: Optional[str] = None):
		if message is None:
			message = f'{gizmo!r}'
		super().__init__(message)
		self.gizmo = gizmo


class MissingGizmo(GadgetFailed, KeyError):
	'''Error for when a gadget fails to grab a gizmo because the gadget can't find it'''
	def __init__(self, gizmo: str, *, message: Optional[str] = None):
		if message is None:
			message = gizmo
		super().__init__(gizmo, message=message)

