from typing import Any, Optional, Iterator, Self, Iterable
from collections import UserDict
from omnibelt import filter_duplicates

from .abstract import (AbstractGadget, AbstractGaggle, AbstractGig, AbstractGang, AbstractGadgetError,
					   AbstractConsistentGig)
from .errors import GadgetFailure, MissingGadget, AssemblyError, GrabError
from .gadgets import GadgetBase
from .gaggles import MutableGaggle, MultiGadgetBase


class GigBase(MultiGadgetBase, GadgetBase, AbstractGig):
	"""
	The GigBase class is a subclass of GadgetBase and AbstractGig. It provides methods to handle gizmo grabbing and packaging.

	Attributes:
		_GrabError (Exception): The exception to be raised when a grab operation fails.
	"""

	_GrabError = GrabError

	def _grab_from_fallback(self, error: Exception, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		"""
		Handles a GadgetFailure when trying to grab a gizmo from the context.

		Args:
			error (Exception): The exception that occurred during the grab operation.
			ctx (Optional[AbstractGig]): The context from which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The result of the fallback operation.

		Raises:
			_GrabError: If the error is a GrabError or if the context is None or self.
			error: If the error is not a GrabError.
		"""
		if isinstance(error, AbstractGadgetError):
			if isinstance(error, GrabError) or ctx is None or ctx is self:
				raise self._GrabError(gizmo, error) from error
			else:
				return ctx.grab(gizmo)
		raise error from error

	def _grab(self, gizmo: str) -> Any:
		"""
		Grabs a gizmo from self.

		Args:
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		return super().grab_from(self, gizmo)

	def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the context.

		Args:
			ctx (Optional[AbstractGig]): The context from which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		try:
			out = self._grab(gizmo)
		except Exception as error:
			out = self._grab_from_fallback(error, ctx, gizmo)
		return self.package(out, gizmo=gizmo)

	def package(self, val: Any, *, gizmo: Optional[str] = None) -> Any:
		"""
		Packages a value with an optional gizmo.

		Args:
			val (Any): The value to be packaged.
			gizmo (Optional[str]): The name of the gizmo. Defaults to None.

		Returns:
			Any: The packaged value.
		"""
		return val


class CacheGig(GigBase, UserDict):
	"""
	The CacheGig class is a subclass of GigBase and UserDict. It provides methods to handle gizmo caching.

	Attributes:
		_gizmo_type (Optional[type]): The type of the gizmo. Defaults to None.
	"""

	_gizmo_type = None

	def __setitem__(self, key, value):
		"""
		Sets an item in the dictionary.

		Args:
			key: The key of the item.
			value: The value of the item.
		"""
		if self._gizmo_type is not None:
			key = self._gizmo_type(key)
		self.set_cache(key, value)

	def set_cache(self, gizmo: str, val: Any):
		"""
		Adds a gizmo and its value to the cache.

		Args:
			gizmo (str): The name of the gizmo to add.
			val (Any): The value of the gizmo to add.
		"""
		self.data[gizmo] = val
		return self

	def __repr__(self):
		"""
		Returns a string representation of the CacheGig instance.

		Returns:
			str: A string representation of the CacheGig instance.
		"""
		gizmos = [(gizmo if self.is_cached(gizmo) else '{' + str(gizmo) + '}') for gizmo in self.gizmos()]
		return f'{self.__class__.__name__}({", ".join(gizmos)})'

	def gizmos(self) -> Iterator[str]:
		"""
		Lists gizmos produced by self.

		Returns:
			Iterator[str]: An iterator over the gizmos.
		"""
		yield from filter_duplicates(self.cached(), super().gizmos())


	def is_cached(self, gizmo: str) -> bool:
		"""
		Checks if a gizmo is cached.

		Args:
			gizmo (str): The name of the gizmo to check.

		Returns:
			bool: True if the gizmo is cached, False otherwise.
		"""
		return gizmo in self.data

	def cached(self) -> Iterator[str]:
		"""
		Lists the cached gizmos.

		Returns:
			Iterator[str]: An iterator over the cached gizmos.
		"""
		yield from self.data.keys()

	def clear_cache(self) -> Self:
		"""
		Clears the cache.
		"""
		self.data.clear()
		return self

	def _cache_miss(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		"""
		Handles a cache miss.

		Args:
			gizmo (str): The name of the gizmo that was not found in the cache.

		Raises:
			AssemblyError: Always.
		"""
		return super().grab_from(ctx, gizmo)

	def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the context.

		Args:
			ctx (Optional[AbstractGig]): The context from which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		if gizmo in self.data:
			return self.data[gizmo]
		val = self._cache_miss(ctx, gizmo)
		self[gizmo] = val  # cache packaged val
		return val


class GroupCache(CacheGig):
	"""
	The GroupCache class is a subclass of CacheGig. It provides methods to handle gizmo caching with group support.

	Attributes:
		_group_cache (dict): A dictionary to store group caches.
	"""

	def __init__(self, *args, group_cache=None, **kwargs):
		"""
		Initializes a new instance of the GroupCache class.

		Args:
			args: Variable length argument list.
			group_cache (Optional[dict]): A dictionary of group caches. If not provided, an empty dictionary will be used.
			kwargs: Arbitrary keyword arguments.
		"""
		if group_cache is None:
			group_cache = {}
		super().__init__(*args, **kwargs)
		self._group_cache = group_cache

	def is_cached(self, gizmo: str) -> bool:
		"""
		Checks if a gizmo is cached in either the main cache or any of the group caches.

		Args:
			gizmo (str): The name of the gizmo to check.

		Returns:
			bool: True if the gizmo is cached, False otherwise.
		"""
		if super().is_cached(gizmo):
			return True
		for group, cache in self._group_cache.items():
			for key in cache:
				if group.gizmo_to(key) == gizmo:
					return True
		return False

	def cached(self) -> Iterator[str]:
		"""
		Lists the cached gizmos in both the main cache and the group caches.

		Returns:
			Iterator[str]: An iterator over the cached gizmos.
		"""
		def _group_cached():
			for group, cache in self._group_cache.items():
				for key in cache:
					yield group.gizmo_to(key)
		yield from filter_duplicates(super().cached(), _group_cached())

	def check_group_cache(self, group: AbstractGang, gizmo: str):
		"""
		Checks a group cache for a gizmo.

		Args:
			group (AbstractGroup): The group to check.
			gizmo (str): The name of the gizmo to check.

		Returns:
			Any: The cached value of the gizmo in the group cache.
		"""
		return self._group_cache[group][gizmo]

	def update_group_cache(self, group: AbstractGang, gizmo: str, val: Any):
		"""
		Updates a group cache with a gizmo and its value.

		Args:
			group (AbstractGroup): The group to update.
			gizmo (str): The name of the gizmo to update.
			val (Any): The value of the gizmo to update.
		"""
		if self._gizmo_type is not None:
			gizmo = self._gizmo_type(gizmo)
		self._group_cache.setdefault(group, {})[gizmo] = val

	def clear_cache(self, *, clear_group_caches=True, **kwargs) -> None:
		"""
		Clears the cache and optionally the group caches.

		Args:
			clear_group_caches (bool): Whether to clear the group caches. Defaults to True.
		"""
		super().clear_cache(**kwargs)
		if clear_group_caches:
			self._group_cache.clear()



class TraceGig(CacheGig):
	"""
	The TraceGig class is a subclass of CacheGig. It provides methods to handle gizmo caching with trace support.
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._history = {} # gizmo -> list of gizmos that were created as a result
		self._products = {} # gizmo -> list of gizmos that used it
		self._partial_grabs = []

	def undo(self, gizmo: str):
		'''removed any cached gizmos that were automatically grabbed during the creation of the given gizmo'''
		self.data.pop(gizmo, None)
		for dep in self._history.pop(gizmo, []):
			# self.data.pop(dep, None)
			self.undo(dep)
		return self

	def purge(self, gizmo: str):
		'''remove any cached gizmo that depends on the given gizmo'''
		self.data.pop(gizmo, None)
		for dep in self._products.pop(gizmo, []):
			# self.data.pop(dep, None)
			self.purge(dep)
		return self

	def _cache_miss(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		self._partial_grabs.append(gizmo)
		try:
			val = super()._cache_miss(ctx, gizmo)
		finally:
			self._partial_grabs.pop()

		if len(self._partial_grabs):
			self._history.setdefault(self._partial_grabs[-1], set()).add(gizmo)
		return val

	def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		val = super().grab_from(ctx, gizmo)
		if len(self._partial_grabs):
			self._products.setdefault(gizmo, set()).add(self._partial_grabs[-1])
		return val



class RollingGig(TraceGig, MutableGaggle):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._rolling_stock = {} # gizmo -> list of gadgets that were included during the gizmos creation


	def rollback(self, gizmo: str):
		'''remove any cached gizmo that depends on the given gizmo'''
		self.exclude(*self._rolling_stock.pop(gizmo, []))
		self.undo(gizmo)
		return self


	def extend(self, gadgets: Iterable[AbstractGadget]) -> Self:
		if len(self._partial_grabs):
			self._rolling_stock.setdefault(self._partial_grabs[-1], []).extend(gadgets)
		return super().extend(gadgets)


	def exclude(self, *gadgets: AbstractGadget) -> Self:
		for known in self._rolling_stock.values():
			for gadget in gadgets:
				if gadget in known:
					known.remove(gadget)
		return super().exclude(*gadgets)



class ConsistentGig(TraceGig, AbstractConsistentGig):
	'''can handle gadgets with multiple outputs (provided those gadgets are deterministic wrt their inputs)'''

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._gadget_precomputes: dict[AbstractGadget,dict[str,Any]] = {} # gadget -> outputs that were already computed (only relevant for gadgets with multiple outputs)

	def clear_cache(self, *, clear_gadget_cache: bool = True, **kwargs) -> None:
		super().clear_cache(**kwargs)
		if clear_gadget_cache:
			self._gadget_precomputes.clear()
		return self

	def set_cache(self, gizmo: str, val: Any):
		if gizmo in self.data and val != self.data[gizmo]:
			self.purge(gizmo)
		return super().set_cache(gizmo, val)

	def is_unchanged(self, gizmo: str):
		return self.is_cached(gizmo) and gizmo in self._products

	def update_gadget_cache(self, gadget: AbstractGadget, cache: dict[str,Any] = None):
		if cache is None:
			self._gadget_precomputes.pop(gadget, None)
		else:
			self._gadget_precomputes.setdefault(gadget, {}).update(cache)
		return self

	def check_gadget_cache(self, gadget: AbstractGadget) -> dict[str, Any]:
		return self._gadget_precomputes.get(gadget, {})









