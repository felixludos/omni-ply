from typing import Optional


class InvalidContextError(TypeError):
	pass



class ToolFailedError(Exception):
	def __init__(self, gizmo: str, message: Optional[str] = None):
		if message is None:
			message = f'{gizmo!r}'
		super().__init__(message)
		self.gizmo = gizmo



class MissingGizmoError(ToolFailedError, KeyError):
	def __init__(self, gizmo: str, message: Optional[str] = None):
		if message is None:
			message = gizmo
		super().__init__(gizmo, message)



class MachineError(MissingGizmoError):
	def __init__(self, gizmo: str, label: str, owner, *, message: Optional[str] = None):
		if message is None:
			message = f'Machine {label} (in {owner}) is missing gizmo {gizmo!r}'
		super().__init__(gizmo, message)



