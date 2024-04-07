from typing import Any, Optional, Iterator
from collections import UserDict
from omnibelt import filter_duplicates

from .abstract import AbstractGate, AbstractGame
from .errors import GadgetFailure, ApplicationAmbiguityError
from .gaggles import GaggleBase, MultiGadgetBase
from .games import GameBase, GatedCache


class GateBase(MultiGadgetBase, GaggleBase, AbstractGate):
	"""
	The GateBase class is a subclass of GaggleBase and AbstractGate. It provides methods to handle gizmo grabbing and packaging.

	Attributes:
		_current_context (Optional[AbstractGame]): The current context of the gate.
	"""

	_current_context: Optional[AbstractGame]

	def __init__(self, *args, gap: Optional[dict[str, str]] = None, **kwargs):
		"""
		Initializes a new instance of the GateBase class.

		Args:
			args: Variable length argument list.
			gap (Optional[dict[str, str]]): A dictionary of gizmo mappings. If not provided, an empty dictionary will be used.
			kwargs: Arbitrary keyword arguments.
		"""
		if gap is None:
			gap = {}
		super().__init__(*args, **kwargs)
		self._raw_gap = gap # internal gizmos -> external gizmos
		self._raw_reverse_gap = None
		self._game_stack = []

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
		return self._raw_gap

	@internal2external.setter
	def internal2external(self, value: dict[str, str]):
		"""
		Setter for the internal to external gizmo mapping.

		Args:
			value (dict[str, str]): The new internal to external gizmo mapping.
		"""
		self._raw_gap = value
		self._raw_reverse_gap = None

	@property
	def external2internal(self) -> dict[str, str]:
		"""
		Getter for the external to internal gizmo mapping.

		Returns:
			dict[str, str]: The external to internal gizmo mapping.
		"""
		if self._raw_reverse_gap is None:
			self._raw_reverse_gap = self._infer_external2internal(self._raw_gap, self._gizmos())
		return self._raw_reverse_gap

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

	def _grab(self, gizmo: str):
		"""
		Grabs a gizmo from self.

		Args:
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		return super().grab_from(self, gizmo)

	def grab_from(self, ctx: AbstractGame, gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the context.

		Args:
			ctx (Optional[AbstractGame]): The context from which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		if ctx is not None and ctx is not self:
			self._game_stack.append(ctx)
			gizmo = self.gizmo_from(gizmo)  # convert to internal gizmo

		try:
			out = self._grab(gizmo)
		except self._GadgetFailure:
			if len(self._game_stack) == 0 or ctx is self._game_stack[-1]:
				raise
			# default to parent/s
			out = self._game_stack[-1].grab(self.gizmo_to(gizmo))

		if len(self._game_stack) and ctx is self._game_stack[-1]:
			self._game_stack.pop()

		return out

	# def _grab_from_fallback(self, error: Exception, ctx: Optional[AbstractGame], gizmo: str) -> Any:
	# 	assert ctx is self, f'{ctx} != {self}'
	# 	if len(self._game_stack):
	# 		return super()._grab_from_fallback(error, self._game_stack[-1], self.gizmo_to(gizmo))
	# 	raise error from error
	#
	#
	# def grab_from(self, ctx: Optional[AbstractGame], gizmo: str) -> Any:
	# 	if ctx is not None and ctx is not self:
	# 		self._game_stack.append(ctx)
	# 		gizmo = self.gizmo_from(gizmo) # convert to internal gizmo
	# 	out = super().grab_from(self, gizmo)
	# 	if len(self._game_stack) and ctx is self._game_stack[-1]:
	# 		self._game_stack.pop()
	# 	return out


class CachableGate(GateBase):
	"""
	The CachableGate class is a subclass of GateBase. It provides methods to handle gizmo grabbing with cache support.

	Attributes:
		_GateCacheMiss (KeyError): The exception to be raised when a cache miss occurs.
	"""

	_GateCacheMiss = KeyError

	def _grab(self, gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the gate. If the gizmo is not found in the gate's cache, it checks the cache using
		the external gizmo name. If it still can't be found in any cache, it grabs it from the gate's gadgets.

		Args:
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		if len(self._game_stack):
			# check cache (if one exists)
			for parent in reversed(self._game_stack):
				if isinstance(parent, GatedCache):
					try:
						return parent.check_gate_cache(self, gizmo)
					except self._GateCacheMiss:
						pass

			# if it can't be found in my cache, check the cache using the external gizmo name
			ext = self.gizmo_to(gizmo)
			for parent in reversed(self._game_stack):
				if isinstance(parent, GatedCache) and parent.is_cached(ext):
					return parent.grab(ext)

		# if it can't be found in any cache, grab it from my gadgets
		out = super()._grab(gizmo)

		# update my cache
		if len(self._game_stack):
			for parent in reversed(self._game_stack):
				if isinstance(parent, GatedCache):
					parent.update_gate_cache(self, gizmo, out)
					break

		return out


class SelectiveGate(GateBase):
	"""
	The SelectiveGate class is a subclass of GateBase. It provides methods to handle selective gizmo mapping.

	Args:
		args: Variable length argument list.
		gap (dict[str, str] | list[str] | None): A dictionary or list of gizmo mappings. If not provided, an empty dictionary will be used.
		kwargs: Arbitrary keyword arguments.
	"""

	def __init__(self, *args, gap: dict[str, str] | list[str] | None = None, **kwargs):
		"""
		Initializes a new instance of the SelectiveGate class.

		If the gap argument is a list, it is converted to a dictionary with the same keys and values.
		If the gap argument is a dictionary, it is processed to ensure that all values are not None.

		Args:
			args: Variable length argument list.
			gap (dict[str, str] | list[str] | None): A dictionary or list of gizmo mappings. If not provided, an empty dictionary will be used.
			kwargs: Arbitrary keyword arguments.
		"""
		if isinstance(gap, list):
			gap = {gizmo: gizmo for gizmo in gap}
		if isinstance(gap, dict):
			gap = {gizmo: gizmo if ext is None else ext for gizmo, ext in gap.items()}
		super().__init__(*args, gap=gap, **kwargs)

	def gizmos(self) -> Iterator[str]:
		"""
		Lists gizmos produced by self using external names.

		Returns:
			Iterator[str]: An iterator over the gizmos.
		"""
		for gizmo in self._gizmos():
			if gizmo in self.internal2external:
				yield self.gizmo_to(gizmo)


