from typing import Optional
from .abstract import AbstractGadgetFailedError


class GadgetFailed(AbstractGadgetFailedError):
	def __init__(self, gizmo: str, *, message: Optional[str] = None):
		if message is None:
			message = f'{gizmo!r}'
		super().__init__(message)
		self.gizmo = gizmo


class MissingGizmoError(GadgetFailed, KeyError):
	def __init__(self, gizmo: str, *, message: Optional[str] = None):
		if message is None:
			message = gizmo
		super().__init__(gizmo, message=message)

