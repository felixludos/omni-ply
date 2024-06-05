







from .gaps import tool, Context, ToolKit, Table, DictGadget


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








