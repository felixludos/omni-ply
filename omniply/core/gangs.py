from typing import Any, Optional, Iterator
from collections import UserDict
from omnibelt import filter_duplicates

from .abstract import AbstractGang, AbstractGig
from .errors import GadgetFailure, ApplicationAmbiguityError
from .gigs import GigBase


class GangBase(GigBase, AbstractGang):
	"""
	The GangBase class is a base for custom gangs to enable remapping the gizmo names.

	Attributes:
		_current_context (Optional[AbstractGig]): The current context associated with this gang.
	"""

	_current_context: Optional[AbstractGig]

	def __init__(self, *, apply: Optional[dict[str, str]] = None, **kwargs):
		"""
		Initializes a new instance of the GangBase class.

		Args:
			apply (Optional[dict[str, str]]): gizmo relabeling. If not provided, an empty dictionary will be used.
			kwargs: unused, passed to super.
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

	@staticmethod
	def _infer_external2internal(raw: dict[str, str], products: Iterator[str]) -> dict[str, str]:
		"""
		Infers the external to internal gizmo mapping (reverse) from the provided raw mapping and products.

		Note, that this method generally shouldn't have to be called by subclasses.

		Args:
			raw (dict[str, str]): The gizmo mapping of internal to external names.
			products (Iterator[str]): An iterator over the products (expected to be `_gizmos`)

		Returns:
			dict[str, str]: The corresponding external to internal gizmo mapping.
		"""
		reverse = {}
		for product in products:
			if product in raw:
				external = raw[product]
				if external in reverse:
					raise ApplicationAmbiguityError(product, [reverse[external], product])
				reverse[external] = product
		return reverse

	def _update_external2internal(self, raw: dict[str, str]):
		self._raw_apply = raw
		self._raw_reverse_apply = None

	def gizmo_from(self, gizmo: str) -> str:
		"""
		Converts an external gizmo to its internal names.

		Used primarily when grabbing a gizmo using self as the context.

		Args:
			gizmo (str): The external gizmo name.

		Returns:
			str: The internal name of the gizmo.
		"""
		if self._raw_reverse_apply is None:
			self._raw_reverse_apply = self._infer_external2internal(self._raw_apply, self._gizmos())
		return self._raw_reverse_apply.get(gizmo, gizmo)

	def gizmo_to(self, gizmo: str) -> str:
		"""
		Converts an internal gizmo to its external representation.

		Used primarily to grab a gizmo from an external context if self fails.

		Args:
			gizmo (str): The internal gizmo name.

		Returns:
			str: The external name of the gizmo.
		"""
		return self._raw_apply.get(gizmo, gizmo)

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


