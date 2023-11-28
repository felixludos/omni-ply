from typing import Any, Optional, Iterator
from collections import UserDict
from omnibelt import filter_duplicates

from .abstract import AbstractGang, AbstractGig
from .errors import GadgetFailure, ApplicationAmbiguityError
from .gigs import GigBase


class GangBase(GigBase, AbstractGang):
	"""
	The GangBase class is a subclass of GigBase and AbstractGang. It provides methods to handle gizmos and their
	internal and external representations.

	Attributes:
	 _current_context (Optional[AbstractGig]): The current context of the gang.
	"""

	_current_context: Optional[AbstractGig]

	def __init__(self, *, apply: Optional[dict[str, str]] = None, **kwargs):
		"""
		Initializes a new instance of the GangBase class.

		Args:
			apply (Optional[dict[str, str]]): A dictionary of gizmo mappings. If not provided, an empty dictionary will be used.
			kwargs: Arbitrary keyword arguments.
		"""
		if apply is None:
			apply = {}
		super().__init__(**kwargs)
		self._raw_apply = apply
		self._raw_reverse_apply = None
		self._current_context = None

	def _gizmos(self) -> Iterator[str]:
		"""
		Lists gizmos produced by self using internal names.

		Returns:
			Iterator[str]: An iterator over the gizmos.
		"""
		yield from super().gizmos()

	def gizmos(self) -> Iterator[str]:
		"""
		Lists gizmos produced by self using external names.

		Returns:
			Iterator[str]: An iterator over the gizmos.
		"""
		for gizmo in self._gizmos():
			yield self.gizmo_to(gizmo)

	@property
	def internal2external(self) -> dict[str, str]:
		"""
		Getter for the internal to external gizmo mapping.

		Returns:
			dict[str, str]: The internal to external gizmo mapping.
		"""
		return self._raw_apply

	@internal2external.setter
	def internal2external(self, value: dict[str, str]):
		"""
		Setter for the internal to external gizmo mapping.

		Args:
			value (dict[str, str]): The new internal to external gizmo mapping.
		"""
		self._raw_apply = value
		self._raw_reverse_apply = None

	@property
	def external2internal(self) -> dict[str, str]:
		"""
		Getter for the external to internal gizmo mapping.

		Returns:
			dict[str, str]: The external to internal gizmo mapping.
		"""
		if self._raw_reverse_apply is None:
			self._raw_reverse_apply = self._infer_external2internal(self._raw_apply, self._gizmos())
		return self._raw_reverse_apply

	@staticmethod
	def _infer_external2internal(raw: dict[str, str], products: Iterator[str]) -> dict[str, str]:
		"""
		Infers the external to internal gizmo mapping from the provided raw mapping and products.

		Args:
			raw (dict[str, str]): The raw gizmo mapping.
			products (Iterator[str]): An iterator over the products.

		Returns:
			dict[str, str]: The inferred external to internal gizmo mapping.
		"""
		reverse = {}
		for product in products:
			if product in raw:
				external = raw[product]
				if external in reverse:
					raise ApplicationAmbiguityError(product, [reverse[external], product])
				reverse[external] = product
		return reverse

	def gizmo_from(self, gizmo: str) -> str:
		"""
		Converts an external gizmo to its internal representation.

		Args:
			gizmo (str): The external gizmo.

		Returns:
			str: The internal representation of the gizmo.
		"""
		return self.external2internal.get(gizmo, gizmo)

	def gizmo_to(self, gizmo: str) -> str:
		"""
		Converts an internal gizmo to its external representation.

		Args:
			gizmo (str): The internal gizmo.

		Returns:
			str: The external representation of the gizmo.
		"""
		return self.internal2external.get(gizmo, gizmo)

	def _grab_from_fallback(self, error: GadgetFailure, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		"""
		Handles a GadgetFailure when trying to grab a gizmo from the context.

		Args:
			error (GadgetFailure): The GadgetFailure that occurred.
			ctx (Optional[AbstractGig]): The context from which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The result of the fallback operation.
		"""
		return super()._grab_from_fallback(error, self._current_context, self.gizmo_to(gizmo))

	def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the context.

		Args:
			ctx (Optional[AbstractGig]): The context from which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		if ctx is not None and ctx is not self and self._current_context is None:
			assert self._current_context is None, f'Context already set to {self._current_context}'
			self._current_context = ctx
		if ctx is self._current_context:
			gizmo = self.gizmo_from(gizmo)  # convert to internal gizmo
		return super().grab_from(self, gizmo)


