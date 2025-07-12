from .imports import *
# from inspect import getattr_static
from .op import Geologist, gem


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



# def test_geode():
#
# 	class Pipeline(Geologist):
# 		model = geode()(input='x', output='z')
# 		criterion = geode(None)(input='z', target='y', output='loss')
#
# 	@tool('output')
# 	def f(input):
# 		return input * 2 - 1
# 	@tool('output')
# 	def squared_error(input, target):
# 		return (input - target) ** 2
# 	@tool('x', 'y')
# 	def data_source():
# 		return 5, 10
#
# 	p = Pipeline(model=f)
#
# 	ctx = Context(p, data_source)
# 	assert ctx['z'] == 9
#
# 	p.criterion = squared_error
# 	ctx = Context(p, data_source)
# 	assert ctx['loss'] == 1





