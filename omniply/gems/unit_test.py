from .imports import *
# from inspect import getattr_static
from ..core import Context, tool, ToolKit
from .op import Geologist, gem, geode


def test_get_order():
	class dec:
		def __init__(self, fn=None):
			pass
		def __call__(self, fn):
			return self
		def __set_name__(self, owner, name):
			self._name = name
		def __get__(self, instance, owner):
			val = instance.__dict__.get(self._name,0) + 1
			instance.__dict__[self._name] = val
			return val
		def __set__(self, instance, value):
			instance.__dict__[self._name] = 2*value

	class A:
		@dec()
		def f(self, x=1):
			return x

	a = A()

	assert a.f == 1
	a.f = 5
	assert a.f == 11



def test_gem():

	class M(Geologist):
		a = gem()
		b = gem(10)

	m = M()

	assert m.b == 10
	m.a = 5
	assert m.a == 5
	m.b = 20
	assert m.b == 20

	m2 = M(a=30)
	assert m2.a == 30
	assert m2.b == 10

	m3 = M(a=-1, b=-2)
	assert m3.a == -1
	assert m3.b == -2
	m3.a = 100
	m3.b = 200
	assert m3.a == 100
	assert m3.b == 200



def test_geode():

	class Pipeline(Geologist, ToolKit):
		model = geode()(input='x', output='z')
		criterion = geode(None)(input='z', target='y', output='loss')

	class MyModel(ToolKit):
		@tool('output')
		def __call__(self, input):
			return input * 2 - 1
	@tool('output')
	def squared_error(input, target):
		return (input - target) ** 2
	@tool('x', 'y')
	def data_source():
		return 5, 10

	p = Pipeline(model=MyModel())

	ctx = Context(p, data_source)
	assert ctx['z'] == 9

	p.criterion = squared_error
	ctx = Context(p, data_source)
	assert ctx['loss'] == 1



def test_config_geode():
	import omnifig as fig
	from ..core import Mechanism

	@fig.component('mod1')
	class Mod1(fig.Configurable, Geologist, ToolKit):
		def __init__(self, a = 10, **kwargs):
			super().__init__(**kwargs)
			self.a = a

		b = gem(100)
		sub = geode(None)(output='x')(input='obs')

		@tool('y')
		def compute_y(self, x):
			return x + self.a
		
		@tool('y2')
		def compute_y2(self, x, other=-1):
			return x + other + self.b
		
	
	@fig.component('mod2')
	class Mod2(fig.Configurable, Geologist, ToolKit):
		b = gem(0)

		@tool('other')
		def compute_other(self, something):
			return something + 10

		@tool('output')
		def compute_fn(self, input):
			return input * self.b


	cfg = fig.create_config(_type='mod1')
	m = cfg.create()
	assert m.a == 10

	cfg = fig.create_config(_type='mod1', a=2, b=30)
	m = cfg.create()
	assert m.a == 2
	assert m.b == 30
	assert m.compute_y(5) == 7

	ctx = Context(m)
	ctx['x'] = 3
	assert ctx['y'] == 5

	cfg = fig.create_config(_type='mod1', b=40, sub=dict(_type='mod2'))

	m = cfg.create()
	assert m.sub.b == 40
	assert m.b == 40
	assert m.sub.compute_fn(5) == 200

	ctx = Context(m)
	assert list(ctx.gizmos()) == ['x', 'y', 'y2']
	ctx['obs'] = 2
	assert ctx['y'] == 90
	assert ctx['y2'] == 119
		



def test_mech_geode():
	import omnifig as fig
	from ..core import Mechanism

	@fig.component('mech')
	class Mech(fig.Configurable, Mechanism):
		def __init__(self, content: Union[AbstractGadget, Iterable[AbstractGadget]] = (), **kwargs):
			if isinstance(content, AbstractGadget):
				content = (content,)
			super().__init__(*content, **kwargs)

	@fig.component('mod1')
	class Mod1(fig.Configurable, Geologist, ToolKit):
		a = gem(10)

		@geode()(output='y', input='x')
		def sub(self):
			@tool('output')
			def default_fn(input):
				return input + self.a
			return default_fn

	@fig.component('mod2')
	class Mod2(fig.Configurable, Geologist, ToolKit):
		b = gem(0)

		@tool('result')
		def __call__(self, initial):
			return initial * b
		
	


def test_config_geode_build():
	import omnifig as fig

	@fig.component('mod1')
	class Mod1(fig.Configurable, Geologist, ToolKit):
		b = gem()
		@b.build
		def fix_b(self, base):
			assert base == 3
			return base * 2
		
	cfg = fig.create_config(_type='mod1', b=3)

	m = cfg.create()
	assert m.b == 6




def test_gem_loop():
	from .errors import ResolutionLoopError

	class Mod1(Geologist):
		@gem()
		def a(self):
			return self.b * 2
		@gem()
		def b(self):
			return self.a - 1

	# m = Mod1()
	#
	# try:
	# 	m.a
	# except ResolutionLoopError:
	# 	pass
	# else:
	# 	assert False, f'shouldve raised a loop error'

	class Mod2(Geologist):
		a = gem(1)
		@gem(10)
		def b(self):
			return self.c * 2
		@gem()
		def c(self):
			return self.a + self.b
	
	m = Mod2()
	assert m.c == 11
	assert m.b == 10
	assert m.a == 1