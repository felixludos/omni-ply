from .imports import *

from .tools import *
from .kits import *
from .contexts import *
from .tools import ToolDecorator as tool



def test_tool():
	@tool('a')
	def f(x):
		return x + 1

	assert f(1) == 2

	@tool('b')
	def g(x, y, z):
		return x + y + z



class TestKit(LoopyKit, MutableKit):
	def __init__(self, *tools: AbstractTool, **kwargs):
		super().__init__(**kwargs)
		self.include(*tools)



class TestContext(Cached, Context, TestKit, AbstractContext):
	pass



def test_kit():
	@tool('y')
	def f(x):
		return x + 1

	@tool('z')
	def g(x, y):
		return x + y

	@tool('y')
	def f2(y):
		return -y

	ctx = TestContext(f, g)

	ctx['x'] = 1
	assert ctx['y'] == 2

	ctx.clear_cache()
	ctx.include(f2)

	ctx['x'] = 1
	assert ctx['y'] == -2



class TestCraftyKit(MutableKit, CraftyKit):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._process_crafts()


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

	assert TestCraftyKit.f(1) == 2
	assert TestCraftyKit.h(1) == 3

	kit = TestCraftyKit()
	assert kit.f(1) == 2
	assert kit.g(1, 2) == 3
	assert kit.h(1) == 3

	ctx = TestContext(kit)

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






