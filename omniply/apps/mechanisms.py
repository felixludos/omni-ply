from typing import Iterable, Iterator, Union, Any, Optional, Mapping
from ..core.abstract import AbstractGate, AbstractGadget, AbstractGame
from ..core.gaggles import LoopyGaggle, MutableGaggle, MultiGadgetBase, GaggleBase
# from ..core.gates import CachableGate, SelectiveGate
from ..core.games import GatedCache
from ..gears.abstract import AbstractGearbox
from ..gears.gearbox import AbstractGeared



class MechanismBase(LoopyGaggle, MutableGaggle, MultiGadgetBase, GaggleBase, AbstractGate):
	def __init__(self, content: Iterable[AbstractGadget] = (), *, insulate_out: bool = True, insulate_in: bool = True,
				 select: Mapping[str, str] = None, apply: Mapping[str, str] = None, **kwargs):
		'''
		insulated: if True, only exposed gizmos are grabbed from parent contexts
		'''
		if select is None:
			select = {}
		if apply is None:
			apply = {}
		super().__init__(**kwargs)
		self.extend(content)
		self._select_map = select # internal gizmos -> external gizmos
		self._apply_map = apply
		self._reverse_select_map = {v: k for k, v in select.items()}
		self._game_stack = []
		self._insulate_out = insulate_out
		self._insulate_in = insulate_in

	# TODO: make sure to update relabels when gadgets are added or removed

	def gizmo_to(self, gizmo: str) -> Optional[str]:
		'''internal -> exposed'''
		return self._select_map.get(gizmo) if self._insulate_out else self._select_map.get(gizmo, gizmo)


	def _gizmos(self) -> Iterator[str]:
		"""
		Lists gizmos produced by self using internal names.

		Returns:
			Iterator[str]: An iterator over the gizmos.
		"""
		yield from super().gizmos()


	def exposed(self) -> Iterator[str]:
		yield from self._apply_map.keys()


	def gizmos(self) -> Iterator[str]:
		for gizmo in self._gizmos():
			if not self._insulate_out or gizmo in self._select_map:
				yield self._select_map.get(gizmo, gizmo)


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
			ext = self._select_map.get(gizmo)
			if ext is not None:
				for parent in reversed(self._game_stack):
					if isinstance(parent, GatedCache) and parent.is_cached(ext):
						return parent.grab(ext)

		# if it can't be found in any cache, grab it from my gadgets
		out = super().grab_from(self, gizmo)

		# update my cache
		if len(self._game_stack):
			for parent in reversed(self._game_stack):
				if isinstance(parent, GatedCache):
					parent.update_gate_cache(self, gizmo, out)
					break

		return out


	def grab_from(self, ctx: AbstractGame, gizmo: str) -> Any:
		"""
		Tries to grab a gizmo from the context.

		Args:
			ctx (Optional[AbstractGame]): The context from which to grab the gizmo.
			gizmo (str): The name of the gizmo to grab.

		Returns:
			Any: The grabbed gizmo.
		"""
		if ctx is None or ctx is self: # internal grab
			fixed = self._apply_map.get(gizmo, gizmo)
			try:
				out = self._grab(fixed)
			except (self._GadgetFailure, self._MissingGadgetError): # important change
				# default to parent/s
				if self._insulate_in and gizmo not in self._apply_map:
					raise
				for parent in reversed(self._game_stack):
					try:
						out = parent.grab(fixed)
					except self._GadgetFailure:
						pass
					else:
						break
				else:
					raise

		else: # grab from external context
			self._game_stack.append(ctx)
			gizmo = self._reverse_select_map.get(gizmo, gizmo)
			out = self._grab(gizmo)

		if len(self._game_stack) and ctx is self._game_stack[-1]:
			self._game_stack.pop()

		return out



class GearedMechanismBase(MechanismBase, AbstractGeared):
	def __init__(self, content, *, insulate_gears_in: bool = None, **kwargs):
		super().__init__(content, **kwargs)
		if insulate_gears_in is None:
			insulate_gears_in = self._insulate_in
		self._insulate_gears_in = insulate_gears_in


	_GearBox = None
	def gearbox(self, insulate_out: bool = True, insulate_in: bool = True,
				 select: Mapping[str, str] = None, apply: Mapping[str, str] = None, **kwargs) -> AbstractGearbox:
		if select is None:
			select = self._select_map
		if apply is None:
			apply = self._apply_map
		if insulate_in is None:
			insulate_in = self._insulate_in
		if insulate_out is None:
			insulate_out = self._insulate_out
		insulate_in = insulate_in or self._insulate_gears_in
		gears = [gadget.gearbox() for gadget in self.vendors() if isinstance(gadget, AbstractGeared)]
		return self._GearBox(gears, insulate_out=insulate_out, insulate_in=insulate_in,
							  select=select, apply=apply, **kwargs)



class UngearedMechanism(MechanismBase):
	def __init__(self, content: Union[AbstractGadget, list[AbstractGadget], tuple],
				 apply: dict[str, str] | list[str] = None,
				 select: dict[str, str] | list[str] = None, **kwargs):
		'''
		apply: map for inputs
		select: relabels for outputs
		'''
		if not isinstance(content, (list, tuple)):
			content = [content]
		if isinstance(apply, list):
			apply = {k: k for k in apply}
		if isinstance(select, list):
			select = {k: k for k in select}
		super().__init__(content=content, apply=apply, select=select, **kwargs)



class Mechanism(UngearedMechanism, GearedMechanismBase):
	_GearBox = UngearedMechanism



class SimpleMechanism(Mechanism):
	def __init__(self, content: Union[AbstractGadget, list[AbstractGadget], tuple], *,
				 insulate_in = None, insulate_out = None,
				 relabel = None, request = None, insulate = True, **kwargs):
		if not isinstance(content, (list, tuple)):
			content = [content]
		if relabel is None:
			relabel = {}
		# select = relabel if request is None else {k: v for k, v in relabel.items() if k in request}
		select = relabel if request is None else {k: relabel.get(k, k) for k in request}
		apply = relabel
		if insulate_in is None:
			insulate_in = insulate
		if insulate_out is None:
			insulate_out = insulate
		super().__init__(content=content, insulate_in=insulate_in, insulate_out=insulate_out,
						 select=select, apply=apply, **kwargs)



