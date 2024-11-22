from typing import Any, Optional, Iterator, Iterable, Mapping, Type, Union

from .abstract import AbstractGate, AbstractGame, AbstractGadget
from .gadgets import GadgetBase
from .gaggles import MultiGadgetBase
from .games import GatedCache, CacheGame



class GangBase(MultiGadgetBase, GadgetBase, AbstractGate):
	def __init__(self, aus: Mapping[str, str] = None, ein: Mapping[str, str] = None, *,
				 exclusive: bool = True, insulated: bool = True, **kwargs):
		"""
		Sets up the ein and aus mappings of this gang.

		Ausgang generally refers to gizmos that are produced by this gang, while eingang refers to the gizmos
		that can be used as inputs (either internally or externally).

		Args:
			aus (Mapping[str, str]): internal gizmos that are exposed by this gang (internal -> external)
			ein (Mapping[str, str]): relabeled gizmos accessible to this gang as inputs (original -> active)
			exclusive (bool, True): If True, only internal gizmos mentioned in `aus` are exposed externally
			insulated (bool, True): If True, only external gizmos mentioned in `ein` are accessible internally
		"""
		if aus is None: aus = {}
		if ein is None: ein = {}
		super().__init__(**kwargs)
		self._aus_gang = aus
		self._reverse_aus_gang = {v: k for k, v in aus.items()}
		if len(self._reverse_aus_gang) != len(aus):
			print(f'WARNING: duplicate external gizmos: {aus}')
		self._ein_gang = ein
		self._gang_stack = [] # of external contexts
		self._exclusive = exclusive
		self._insulated = insulated

	def gizmo_to(self, internal: str) -> Optional[str]:
		"""
		Converts an internal gizmo to its external representation.

		Returns None if the gizmo is not exposed.
		"""
		return self._aus_gang.get(internal, None if self._exclusive else internal)


	def gizmo_from(self, external: str) -> Optional[str]:
		"""
		Converts an external gizmo to its internal representation.

		Returns None if the gizmo is not accessible.
		"""
		return self._reverse_aus_gang.get(external)


	def dependencies(self) -> Iterator[str]: # TODO: is this necessary? principled?
		"""
		Lists gizmos that may be accessed by this gang from external contexts.

		using their external names. Crucially this filters out all the gizmos that can be produced "inhouse"
		"""
		inhouse = set(self._gizmos())
		for req in self._ein_gang.values():
			if req not in inhouse:
				yield req


	def gizmos(self) -> Iterator[str]:
		"""
		Lists gizmos produced by self using external names.

		Returns:
			Iterator[str]: An iterator over the gizmos.
		"""
		for internal in self._gizmos():
			external = self.gizmo_to(internal)
			if external is not None:
				yield external


	def _gizmos(self) -> Iterator[str]:
		"""
		Lists gizmos produced by self using internal names.

		Returns:
			Iterator[str]: An iterator over the gizmos.
		"""
		yield from super().gizmos()


	def _grab(self, internal: str) -> Any:
		"""
		Internal grab the gizmo

		Args:
			gizmo (str): The name of the gizmo to grab using the internal name

		"""
		return super().grab_from(self, internal)


	def grab_from(self, ctx: AbstractGame, gizmo: str) -> Any:
		"""
		Resolves both internal and external grabs.

		Args:
			ctx (Optional[AbstractGame]): The context from which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		if ctx is None or ctx is self: # internal grab
			internal = self._ein_gang.get(gizmo, gizmo)
			try:
				out = self._grab(internal)
			except (self._GadgetFailure, self._MissingGadgetError):
				# default to parent/s
				if self._insulated and gizmo not in self._ein_gang:
					raise
				for parent in reversed(self._gang_stack):
					try:
						out = parent.grab(internal)
					except self._GadgetFailure:
						pass
					else:
						break
				else:
					raise

		else: # was called from an external context
			self._gang_stack.append(ctx)
			gizmo = self._reverse_aus_gang.get(gizmo, gizmo)
			out = self._grab(gizmo)

		if len(self._gang_stack) and ctx is self._gang_stack[-1]:
			self._gang_stack.pop()

		return out



class GateBase(GangBase):
	"""A simplified gang that only relabels gizmos"""
	def __init__(self, select: Iterable[str] = None, gate: Mapping[str, str] = None, *,
				 exclusive: bool = None, insulated: bool = None, **kwargs):
		"""
		Initializes a gate, which is a simplified gang.

		Args:
			select (Iterable[str]): Internal gizmos that should be made accessible externally
			gate (Mapping[str, str]): Mapping of original gizmo names -> updated gizmo names (used both internally and externally)
			exclusive (bool): If True, only the selected gizmos are exposed externally
			insulated (bool): If True, only the relabeled gizmos are accessible internally

		"""
		if insulated is None: insulated = gate is not None
		if exclusive is None: exclusive = select is not None
		if gate is None: gate = {}
		aus = gate if select is None else {k: gate.get(k, k) for k in select}
		ein = gate
		assert 'aus' not in kwargs and 'ein' not in kwargs, f'{kwargs}'
		super().__init__(aus=aus, ein=ein, exclusive=exclusive, insulated=insulated, **kwargs)



class CachableGang(GangBase):
	_GateCacheMiss = KeyError # TODO: create a dedicated subclass for this exception
	def _grab(self, gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the gang using the caches

		If the gizmo is not found in the gang's cache, it checks the cache using the external gizmo name.
		If it still can't be found in any cache, it grabs it from the gang's gadgets.

		Args:
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		if len(self._gang_stack):
			# check cache (if one exists)
			ext = self.gizmo_to(gizmo)
			for parent in reversed(self._gang_stack):
				if isinstance(parent, GatedCache):
					try:
						return parent.check_gate_cache(self, gizmo)
					except self._GateCacheMiss:
						pass
				# if it can't be found in my cache, check the cache using the external gizmo name
				if ext is not None and isinstance(parent, CacheGame) and parent.is_cached(ext):
					return parent.grab(ext)

		# if it can't be found in any cache, grab it from my gadgets
		out = super()._grab(gizmo)

		# update my cache
		if len(self._gang_stack):
			for parent in reversed(self._gang_stack):
				if isinstance(parent, GatedCache):
					parent.update_gate_cache(self, gizmo, out)
					break

		return out



