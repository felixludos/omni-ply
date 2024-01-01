from typing import Any, Optional, Iterator
from collections import UserDict
from omnibelt import filter_duplicates

from .abstract import AbstractGadget, AbstractGaggle, AbstractGig, AbstractGang, AbstractGadgetError
from .errors import GadgetFailure, MissingGadget, AssemblyError, GrabError
from .gadgets import GadgetBase


class GigBase(GadgetBase, AbstractGig):
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
		super().__setitem__(key, value)

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

	def clear_cache(self) -> None:
		"""
		Clears the cache.
		"""
		self.data.clear()

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
		val = super().grab_from(ctx, gizmo)
		self.data[gizmo] = val  # cache packaged val
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

	def clear_cache(self, *, clear_group_caches=True) -> None:
		"""
		Clears the cache and optionally the group caches.

		Args:
			clear_group_caches (bool): Whether to clear the group caches. Defaults to True.
		"""
		super().clear_cache()
		if clear_group_caches:
			self._group_cache.clear()

