from typing import Iterable, Iterator, Union, Any, Optional, Mapping
from ..core.abstract import AbstractGate, AbstractGadget, AbstractGame
from ..core.gaggles import LoopyGaggle, MutableGaggle, MultiGadgetBase, GaggleBase
from ..core.gates import CachableGate, SelectiveGate
from ..core.games import GatedCache



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
			except self._GadgetFailure:
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



class Mechanism(MechanismBase):
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



class SimpleMechanism(Mechanism):
	def __init__(self, content: Union[AbstractGadget, list[AbstractGadget], tuple], *,
				 insulate_in = None, insulate_out = None,
				 relabel = None, request = None, insulate = True, **kwargs):
		if not isinstance(content, (list, tuple)):
			content = [content]
		if relabel is None:
			relabel = {}
		select = relabel if request is None else {k: v for k, v in relabel.items() if k in request}
		apply = relabel
		if insulate_in is None:
			insulate_in = insulate
		if insulate_out is None:
			insulate_out = insulate
		super().__init__(content=content, insulate_in=insulate_in, insulate_out=insulate_out,
						 select=select, apply=apply, **kwargs)



def test_simple_mechanism():
	from ..core import ToolKit, tool, Context, Scope
	from .simple import DictGadget

	# Mechanism = Scope

	class Tester(ToolKit):
		@tool('out')
		def f(self, in1, in2):
			return in1 - in2

	obj = Tester()

	ctx = Context(obj, DictGadget({'in1': 10, 'in2': 7, 'alt': 1}))

	ctx.include(SimpleMechanism(obj, relabel={'out': 'out2', 'in2': 'alt'}, insulate=False))

	gizmos = list(ctx.gizmos())
	assert 'out' in gizmos, f'out not in {gizmos}'
	assert 'out2' in gizmos, f'out2 not in {gizmos}'

	assert ctx['out'] == 3
	assert ctx.is_cached('in1') and ctx.is_cached('in2')
	assert ctx.is_cached('out')
	assert not ctx.is_cached('out2')

	assert ctx['out2'] == 9
	assert ctx.is_cached('out2')

	ctx.clear()

	assert ctx['out2'] == 9
	assert not ctx.is_cached('out')

def test_insulated_mechanism():

	from ..core import ToolKit, tool, Context, Scope
	from .simple import DictGadget

	class Tester(ToolKit):
		@tool('intermediate')
		def f(self, in1, in2):
			return in1 - in2

		@tool('out')
		def g(self, intermediate):
			return -intermediate

	obj = Tester()

	ctx = Context(obj, DictGadget({'in1': 10, 'in2': 7, 'alt': 1}))

	ctx.clear()

	mech = SimpleMechanism(obj, relabel={'out': 'out2', 'in2': 'alt'}, insulate_in=False)

	ctx.include(mech)

	gizmos = list(ctx.gizmos())
	assert 'out2' in gizmos, f'out2 not in {gizmos}'

	assert ctx['out'] == -3, f'{ctx["out"]} != -3'
	assert ctx['out2'] == -9, f'{ctx["out2"]} != -9'

	ctx.clear()

	assert ctx['out2'] == -9, f'{ctx["out2"]} != -9'
	assert ctx['out'] == -3, f'{ctx["out"]} != -3'

	@tool('alt2')
	def other_alt():
		return 5

	mech = SimpleMechanism(obj, relabel={'out': 'out2', 'in2': 'alt2', 'in1': 'alt2'})

	ctx = Context(mech, other_alt)

	assert ctx['out2'] == 0

def test_chain():
	from ..core import ToolKit, tool, Context, Scope
	from .simple import DictGadget

	class Tester(ToolKit):
		@tool('b')
		def f(self, a):
			return a + 1

		@tool('d')
		def g(self, c):
			return -c

	src = Tester()

	obj = SimpleMechanism(src, relabel={'b': 'c', 'd': 'd'}, insulate_in=False)
	ctx = Context(obj, DictGadget({'a': 1}))
	assert ctx['d'] == -2

	# This works but is worse as it requires the 'b': 'b' to make b visible externally
	obj = SimpleMechanism(src, relabel={'c': 'b', 'b': 'b', 'd': 'd'}, insulate_in=False)
	ctx = Context(obj, DictGadget({'a': 2}))
	assert ctx['d'] == -3

def test_multi_chain():
	from .gaps import ToolKit, tool, Context
	from .simple import DictGadget

	class Tester(ToolKit):
		@tool('b')
		def f(self, a):
			return a + 1

		@tool('d')
		def g(self, c):
			return -c

	src = Tester(gap={'b': 'c'})

	obj = SimpleMechanism(src, relabel={'d': 'e', 'c': 'alt'}, request=['d'])
	obj2 = SimpleMechanism(src, relabel={'c': 'f', 'a': 'alt'})
	ctx = Context(obj, obj2, src, DictGadget({'a': 1, 'alt': -4}))

	assert ctx['d'] == -2
	assert ctx['e'] == 4
	assert ctx['f'] == -3

def test_break_chain():
	from .gaps import ToolKit, tool, Context
	from .simple import DictGadget

	class Tester(ToolKit):
		@tool('b')
		def f(self, a):
			return a + 1

		@tool('c')
		def g(self, b):
			return -b

	src = Tester()

	obj = SimpleMechanism(src, relabel={'c': 'd', 'b': 'other'}, request=['c'])
	obj2 = SimpleMechanism(src, relabel={'b': 'e', 'a': 'other2', 'c': 'f'})
	ctx = Context(obj, obj2, src, DictGadget({'a': 1, 'other': 10, 'other2': 100}))

	assert ctx['c'] == -2
	assert ctx['d'] == -10
	assert ctx['f'] == -101
	assert ctx['e'] == 101

def test_rebuild_chain():
	from .gaps import ToolKit, tool, Context
	from .simple import DictGadget

	class Tester(ToolKit):
		@tool('lat')
		def f(self, obs):
			return obs + 1

		@tool('rec')
		def g(self, lat):
			return -lat

	src = Tester()

	resp = Mechanism([src], select={'lat': 'response'}, relabel_in={'obs': 'rec', 'lat': 'probe'})
	resp2 = Mechanism([src], select={'lat': 'resp2', 'rec': 'prec'},
					  relabel_in={'obs': 'rec', 'lat': 'probe2'})
	ctx = Context(src, resp, resp2, DictGadget({'obs': 1, 'probe': 10, 'probe2': 100}))

	assert ctx['rec'] == -2
	assert ctx['response'] == -9
	assert ctx['resp2'] == -99
	assert ctx['prec'] == -100


