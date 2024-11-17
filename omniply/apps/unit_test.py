from .gaps import tool, Context, ToolKit, Table, DictGadget
from .mechanisms import SimpleMechanism, Mechanism


# region Gauges and Gaps

def test_gauge():

	class Kit1(ToolKit):
		@tool('a')
		def f(self, x, y):
			return x + y

	@tool('b')
	def g(x, y):
		return x - y

	kit = Kit1()

	assert list(kit.gizmos()) == ['a']

	kit.gauge_apply({'a': 'z'})

	assert list(kit.gizmos()) == ['z']

	ctx = Context(kit, g)

	assert list(ctx.gizmos()) == ['z', 'b']

	ctx.gauge_apply({'b': 'w'})

	assert list(ctx.gizmos()) == ['z', 'w']
	assert list(g.gizmos()) == ['w']

	ctx['x'] = 1
	ctx['y'] = 2

	ctx.gauge_apply({'x': 'c'})

	assert ctx['c'] == 1
	assert ctx['w'] == -1
	assert ctx['z'] == 3

	assert ctx.grab('a', None) is None
	assert ctx.grab('b', None) is None



def test_gapped_tools():

	class Kit(ToolKit):
		@tool.from_context('x', 'y')
		def f(self, game):
			return game[self.gap('a')], game[self.gap('b')] + game[self.gap('c')]
		@f.parents
		def _f_parents(self):
			return map(self.gap, ['a', 'b', 'c'])


	kit = Kit(gap={'a': 'z'})

	assert list(kit.gizmos()) == ['x', 'y']

	ctx = Context(kit)

	ctx.update({'z': 1, 'b': 2, 'c': 3})

	assert ctx['x'] == 1 and ctx['y'] == 5

	gene = next(kit.genes('x'))

	assert gene.parents == ('z', 'b', 'c')



def test_double_gap():
	@tool('a', 'b')
	def f(x, y):
		return x + y, x - y

	ctx = Context(f, DictGadget({'x': 10, 'y': 2}))

	assert list(ctx.gizmos()) == ['a', 'b', 'x', 'y']
	assert ctx['a'] == 12
	ctx.clear_cache()

	ctx.gauge_apply({'a': 'z'}) # a becomes z

	assert list(ctx.gizmos()) == ['z', 'b', 'x', 'y']
	assert ctx['z'] == 12
	ctx.clear_cache()

	ctx.gauge_apply({'z': 'zz'})

	assert list(ctx.gizmos()) == ['zz', 'b', 'x', 'y']
	assert ctx['zz'] == 12
	ctx.clear_cache()



def test_gapped_apps():

	d = DictGadget({'a': 1}, {'b': 2}, c=10)

	ctx = Context(d)

	assert list(ctx.gizmos()) == ['c', 'a', 'b']

	ctx.gauge_apply({'a': 'x', 'c': 'y'})

	assert list(ctx.gizmos()) == ['y', 'x', 'b']


	tbl = Table({'a': [1, 2, 3], 'b': [4, 5, 6]})

	tbl.gauge_apply({'a': 'z'})

	ctx = Context(tbl, DictGadget({'index': 0}))

	assert ctx['z'] == 1
	assert ctx['b'] == 4

# endregion

# region Mechanism

def test_simple_mechanism():
	# from ..core import ToolKit, tool, Context

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

# endregion




