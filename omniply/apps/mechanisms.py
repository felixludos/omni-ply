from typing import Iterable, Iterator, Union
from ..core.abstract import AbstractGate, AbstractGadget
from ..core.gaggles import LoopyGaggle, MutableGaggle
from ..core.gates import CachableGate, SelectiveGate

from ..core import Scope, Selection


class MechanismBase(SelectiveGate, CachableGate, LoopyGaggle, MutableGaggle, AbstractGate):
	def __init__(self, content: Iterable[AbstractGadget] = (), *,
				 insulate: bool = True, gate: dict[str, str] | list[str] | None = None, **kwargs):
		super().__init__(gate=gate, **kwargs)
		self._insulate_gizmos = insulate
		self.extend(content)


	def gizmos(self) -> Iterator[str]:
		for gizmo in self._gizmos():
			if not self._insulate_gizmos or gizmo in self.internal2external:
				yield self.gizmo_to(gizmo)


	def gizmo_to(self, gizmo: str) -> str:
		return self.internal2external.get(gizmo)



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

	ctx.include(Mechanism(obj, gate={'out': 'out2', 'in2': 'alt'}))

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

	mech = Mechanism(obj, gate={'out': 'out2', 'in2': 'alt'})

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

	mech = Mechanism(obj, gate={'out': 'out2', 'in2': 'alt2', 'in1': 'alt2'})

	ctx = Context(mech, other_alt)

	assert ctx['out2'] == 0





