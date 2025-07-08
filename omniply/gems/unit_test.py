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
# 	class M(Geologist):
# 		sub1 = geode()(input='x', output='z')
# 		sub2 = geode(None)(input='z', target='y', output='loss')





