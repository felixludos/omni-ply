from .abstract import AbstractGizmo


class DashGizmo(AbstractGizmo):
	"""
	The DashGizmo class is a subclass of AbstractGizmo. It provides methods to handle gizmos with dashes.

	Attributes:
		_native (str): The original label of the gizmo.
		_fixed (str): The label of the gizmo with dashes replaced by underscores.
	"""

	__slots__ = ('_native', '_fixed')

	def __init__(self, label: str):
		"""
		Initializes a new instance of the DashGizmo class.

		Args:
			label (str): The label of the gizmo.
		"""
		self._native = label
		self._fixed = label.replace('-', '_')

	def __eq__(self, other):
		"""
		Checks if the DashGizmo instance is equal to another object.

		Args:
			other: The object to compare with.

		Returns:
			bool: True if the DashGizmo instance is equal to the other object, False otherwise.
		"""
		if isinstance(other, str):
			return str(self) == other.replace('-', '_')
		return str(self) == str(other)

	def __hash__(self):
		"""
		Returns the hash of the DashGizmo instance.

		Returns:
			int: The hash of the DashGizmo instance.
		"""
		return hash(str(self))

	def __str__(self):
		"""
		Returns a string representation of the DashGizmo instance.

		Returns:
			str: A string representation of the DashGizmo instance.
		"""
		return self._fixed












