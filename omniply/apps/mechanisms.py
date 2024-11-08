from typing import Iterable, Iterator, Union, Any, Optional, Mapping
from ..core.abstract import AbstractGate, AbstractGadget, AbstractGame
from ..core.gaggles import LoopyGaggle, MutableGaggle, MultiGadgetBase, GaggleBase
from ..core.gates import CachableGate, SelectiveGate
from ..core.games import GatedCache



class MechanismBase(LoopyGaggle, MutableGaggle, MultiGadgetBase, GaggleBase, AbstractGate):
	def __init__(self, content: Iterable[AbstractGadget] = (), *, relabel: Mapping[str, str] = None,
				 request: Optional[Iterable[str]] = None, insulate: bool = True, **kwargs):
		'''
		insulated: if True, only exposed gizmos are grabbed from parent contexts
		'''
		if relabel is None:
			relabel = {}
		super().__init__(**kwargs)
		self.extend(content)
		self._relabel = relabel # internal gizmos -> external gizmos
		available = set(self._gizmos())
		self._reverse_relabel = {v: k for k, v in relabel.items() if k in available}
		self._game_stack = []
		self._request = request
		self._insulate_gizmos = insulate

	# TODO: make sure to update relabels when gadgets are added or removed

	def gizmo_to(self, gizmo: str) -> Optional[str]:
		'''internal -> exposed'''
		return self._relabel.get(gizmo)


	def _gizmos(self) -> Iterator[str]:
		"""
		Lists gizmos produced by self using internal names.

		Returns:
			Iterator[str]: An iterator over the gizmos.
		"""
		yield from super().gizmos()


	def exposed(self) -> Iterator[str]:
		for gizmo in self._gizmos():
			if self._request is None or gizmo in self._request:
				yield gizmo


	def gizmos(self) -> Iterator[str]:
		for gizmo in self._gizmos():
			if self._request is None or gizmo in self._request:
				yield self._relabel.get(gizmo, gizmo)


	def expose(self, label: str, gizmo: str):
		"""
		Expose a gizmo under a different label.

		Args:
			label (str): The label to expose the gizmo under.
			gizmo (str): The gizmo to expose.
		"""
		self._relabel[label] = gizmo
		# TODO: update reverse relabel
		raise NotImplementedError


	def expected(self, gizmo: str) -> Iterator[str]:
		'''
		generates all the gizmos that are required to produce `gizmo` except for the ones that
		are explicitly mentioned
		'''
		raise NotImplementedError


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
			ext = self._relabel.get(gizmo)
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
		original = gizmo
		if ctx is None or ctx is self:
			gizmo = self._relabel.get(gizmo, gizmo)
		else:
			self._game_stack.append(ctx)
			gizmo = self._reverse_relabel.get(gizmo, gizmo)

		try:
			out = self._grab(gizmo)
		except self._GadgetFailure:
			if len(self._game_stack) == 0 or ctx is self._game_stack[-1]:
				raise
			# default to parent/s
			ext = self._relabel.get(original)
			if ext is None:
				if self._insulate_gizmos:
					raise
				else:
					ext = gizmo
			for parent in reversed(self._game_stack):
				try:
					out = parent.grab(ext)
				except self._GadgetFailure:
					pass
				else:
					break
			else:
				raise

		if len(self._game_stack) and ctx is self._game_stack[-1]:
			self._game_stack.pop()

		return out



class Mechanism(MechanismBase):
	def __init__(self, content: Union[AbstractGadget, list[AbstractGadget], tuple], **kwargs):
		if not isinstance(content, (list, tuple)):
			content = [content]
		super().__init__(content=content, **kwargs)



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

	ctx.include(Mechanism(obj, relabel={'out': 'out2', 'in2': 'alt'}))

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

	mech = Mechanism(obj, relabel={'out': 'out2', 'in2': 'alt'})

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

	mech = Mechanism(obj, relabel={'out': 'out2', 'in2': 'alt2', 'in1': 'alt2'})

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

	obj = Mechanism(src, relabel={'b': 'c', 'd': 'd'})
	ctx = Context(obj, DictGadget({'a': 1}))
	assert ctx['d'] == -2

	# This works but is worse as it requires the 'b': 'b' to make b visible externally
	obj = Mechanism(src, relabel={'c': 'b', 'b': 'b', 'd': 'd'})
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

	obj = Mechanism(src, relabel={'d': 'e', 'c': 'alt'}, request=['d'])
	obj2 = Mechanism(src, relabel={'c': 'f', 'a': 'alt'})
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

	obj = Mechanism(src, relabel={'c': 'd', 'b': 'other'}, request=['c'])
	obj2 = Mechanism(src, relabel={'b': 'e', 'a': 'other2', 'c': 'f'})
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

	resp = FullMechanism(src, relabel_out={'lat': 'response'}, relabel_inp={'obs': 'rec', 'lat': 'probe'})
	ctx = Context(src, resp, DictGadget({'obs': 1, 'probe': 10}))

	assert ctx['rec'] == -2
	assert ctx['response'] == -9


