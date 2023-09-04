from .top import tool, ToolKit, Context, Scope



def test_tool():
	@tool('a')
	def f(x):
		return x + 1

	assert f(1) == 2

	@tool('b')
	def g(x, y, z):
		return x + y + z

	assert list(g.gizmos()) == ['b'], f'gizmos: {list(g.gizmos())}'



def test_context():
	@tool('y')
	def f(x):
		return x + 1

	@tool('z')
	def g(x, y):
		return x + y

	@tool('y')
	def f2(y):
		return -y

	ctx = Context(f, g)

	ctx['x'] = 1
	assert ctx['y'] == 2

	ctx.clear_cache()
	ctx.include(f2)

	ctx['x'] = 1
	assert ctx['y'] == -2



class _Kit1(ToolKit):
	@tool('y')
	@staticmethod
	def f(x):
		return x + 1

	@tool('z')
	def g(self, x, y):
		return x + y

	@tool('w')
	@classmethod
	def h(cls, z):
		return z + 2



def test_crafty_kit():
	assert _Kit1.f(1) == 2
	assert _Kit1.h(1) == 3

	kit = _Kit1()
	assert kit.f(1) == 2
	assert kit.g(1, 2) == 3
	assert kit.h(1) == 3

	ctx = Context(kit)

	assert list(ctx.gizmos()) == ['y', 'z', 'w']

	ctx['x'] = 1
	assert ctx['y'] == 2
	ctx['y'] = 3
	assert ctx['y'] == 3
	assert ctx['z'] == 4
	assert ctx['w'] == 6

	ctx.clear_cache()
	ctx['x'] = 10
	assert ctx['z'] == 21
	assert ctx['w'] == 23



class _Kit2(_Kit1): # by default inherits all tools from the parents
	def __init__(self, sign=1):
		super().__init__()
		self._sign = sign

	@tool('y') # tool replaced
	def change_y(self, y): # "refinement" - chaining the tool implicitly
		return y + 10

	@tool('x') # new tool added
	def get_x(self):
		return 100 * self._sign # freely use object attributes

	def check(self): # freely calling tools as methods
		return self.f(9) + type(self).h(8) + type(self).f(19) # 40

	@tool('z')
	def g(self, x): # overriding a tool (this will be registered, rather than the super method)
		# use with caution - it's recommended to use clear naming for the function
		return super().g(x, x) # super method can be called as usual



def test_crafty_kit_inheritance():

	assert _Kit2.f(1) == 2
	assert _Kit2.h(1) == 3

	kit = _Kit2()
	assert kit.f(1) == 2
	assert kit.g(2) == 4
	assert kit.h(1) == 3
	assert kit.check() == 40
	assert kit.get_x() == 100
	assert kit.change_y(1) == 11

	ctx = Context(kit)

	assert list(ctx.gizmos()) == ['y', 'z', 'w', 'x']

	assert ctx['x'] == 100
	assert ctx['y'] == 111
	assert ctx['z'] == 200
	assert ctx['w'] == 202

	ctx.clear_cache()

	new_z = tool('z')(lambda: 1000)
	ctx.include(new_z)

	assert 'x' not in ctx.cached()
	assert ctx['y'] == 111
	assert 'x' in ctx.cached()
	assert ctx['x'] == 100

	assert ctx['z'] == 1000
	assert ctx['w'] == 1002


class _Kit3(ToolKit):
	@tool('b')
	@tool('a')
	def f(self):
		return 1

	@tool('c')
	@tool('b')
	def g(self):
		return 2

	@tool('d')
	@tool('c')
	def h(self, b):
		return b + 10


def test_nested_tools():

	kit = _Kit3()

	assert list(kit.gizmos()) == ['a', 'b', 'c', 'd']

	ctx = Context(kit)

	assert ctx['d'] == 11
	assert ctx['c'] == 2
	assert ctx['b'] == 1
	assert ctx['a'] == 1



def test_scope():

	kit = _Kit1()

	scope = Scope(kit,
				  apply={'y': 'a'})

	assert list(scope.gizmos()) == ['a', 'z', 'w']

	ctx = Context(scope)

	assert list(ctx.gizmos()) == ['a', 'z', 'w']

	ctx['x'] = 1
	assert ctx['a'] == 2

	ctx = Context(Scope(kit, apply={'y': 'a', 'x': 'b'}))

	assert list(ctx.gizmos()) == ['a', 'z', 'w']

	ctx['b'] = 1
	assert ctx['a'] == 2
	assert ctx['z'] == 3


# TODO: test group cache





