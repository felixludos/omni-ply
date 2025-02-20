from .gaps import tool, Context, Structured, ToolKit, gear, Table, DictGadget
from .. import Gate, Mechanism
from .simple import flag, cond

# region Flags and Conds

def test_flag():

	class K1(ToolKit):
		@flag('a')
		def f(self):
			return True
		
		@flag('b')
		def g(self, x=0):
			return x > 0
		
	class K2(ToolKit):
		@flag('a')
		def h(self, y=0):
			raise Exception('Should not be called')
		
		@flag('b')
		def i(self, y=0):
			assert y >= 0
			return y > 0


	k1 = K1()
	k2 = K2()

	ctx = Context(k1, k2)

	assert ctx['a'] is True
	assert ctx['b'] is False
	
	ctx.clear_cache()
	ctx['x'] = 1
	ctx['y'] = -1

	assert ctx['b'] is True

	ctx.clear_cache()
	ctx['x'] = -10
	ctx['y'] = 1

	assert ctx['b'] is True




# endregion

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

	d = DictGadget({'c':10, 'a': 1, 'b': 2})

	ctx = Context(d)

	assert list(ctx.gizmos()) == ['c', 'a', 'b']

	ctx.gauge_apply({'a': 'x', 'c': 'y'})

	assert list(ctx.gizmos()) == ['y', 'x', 'b']


	tbl = Table({'a': [1, 2, 3], 'b': [4, 5, 6]})

	tbl.gauge_apply({'a': 'z'})

	ctx = Context(tbl, DictGadget({'index': 0}))

	assert ctx['z'] == 1
	assert ctx['b'] == 4



def test_gapped_gear():
	class Tester(Structured):
		@gear('a')
		def something(self):
			return 10

		@gear('b')
		def something_else(self, a):
			return a + 5

	src = Tester(gap={'a': 'c'}).mechanize()

	assert src.something == 10
	assert src.something_else == 15

	assert src.mechanics().is_cached('c')
	assert src.mechanics()['b'] == 15



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

	obj = Gate(src, gate={'d': 'e', 'c': 'alt'}, select=['d'])
	obj2 = Gate(src, gate={'c': 'f', 'a': 'alt'}, exclusive=True)
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

	obj = Gate(src, gate={'c': 'd', 'b': 'other'}, select=['c'])
	obj2 = Gate(src, gate={'b': 'e', 'a': 'other2', 'c': 'f'}, exclusive=True)
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

	resp = Mechanism(src, external={'lat': 'response'}, internal={'obs': 'rec', 'lat': 'probe'})
	resp2 = Mechanism(src, external={'lat': 'resp2', 'rec': 'prec'},
					  internal={'obs': 'rec', 'lat': 'probe2'})
	ctx = Context(src, resp, resp2, DictGadget({'obs': 1, 'probe': 10, 'probe2': 100}))

	assert ctx['rec'] == -2
	assert ctx['response'] == -9
	assert ctx['resp2'] == -99
	assert ctx['prec'] == -100


# endregion




