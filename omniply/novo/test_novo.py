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






