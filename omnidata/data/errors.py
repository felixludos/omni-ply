

from ..tools.errors import MissingGizmoError


class UnknownSize(TypeError):
	def __init__(self):
		super().__init__('did you forget to provide a "default_len" in __init__?')


class MissingBuffer(MissingGizmoError):
	pass



