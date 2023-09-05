from .abstract import AbstractGizmo



class DashGizmo(AbstractGizmo):
	__slots__ = ('_native', '_fixed')


	def __init__(self, label: str):
		self._native = label
		self._fixed = label.replace('-', '_')


	def __eq__(self, other):
		if isinstance(other, str):
			return str(self) == other.replace('-', '_')
		return str(self) == str(other)


	def __hash__(self):
		return hash(str(self))


	def __str__(self):
		return self._fixed














