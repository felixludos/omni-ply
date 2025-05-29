from .imports import *
from .op import Context, ToolKit, Structured, gear, Mechanics, Mechanized, Mechanism, Gate
from .. import GrabError, tool
from .errors import GearFailed


def test_gears():

	class Tester(ToolKit):
		@gear('a')
		def something(self):
			return 10

		@gear('b')
		def something_else(self, a):
			return a + 5

	src = Tester()

	assert src.something == 10
	assert src.something_else == 15

	src.something = 20

	assert src.something == 20



def test_auto_mechanized(): # subclassing Mechanized automatically mechanizes
	class Flag(Exception): pass

	class Tester(Mechanized, Structured):
		allow_a_once = True
		allow_b_once = True

		@gear('a')
		def something(self):
			if not self.allow_a_once:
				raise Flag
			self.allow_a_once = False
			return 10

		@gear('b')
		def something_else(self, a):
			if not self.allow_b_once:
				raise Flag
			self.allow_b_once = False
			return a + 5

	src = Tester()

	assert src.allow_a_once and src.allow_b_once
	assert src.something_else == 15

	assert not src.allow_a_once and not src.allow_b_once
	assert src.something == 10
	assert src.something_else == 15

	mech = src.mechanics()

	assert mech.is_cached('a') and mech.is_cached('b')

	mech.clear_cache()

	try:
		src.something
		assert False
	except Flag:
		pass


def test_manual_mechanized():
	class Flag(Exception): pass

	class Tester(Structured):
		allow_a_once = True
		allow_b_once = True

		@gear('a')
		def something(self):
			if not self.allow_a_once:
				raise Flag
			self.allow_a_once = False
			return 10

		@gear('b')
		def something_else(self, a):
			if not self.allow_b_once:
				raise Flag
			self.allow_b_once = False
			return a + 5

	src = Tester()
	src.mechanize()

	assert src.allow_a_once and src.allow_b_once
	assert src.something_else == 15

	assert not src.allow_a_once and not src.allow_b_once
	assert src.something == 10
	assert src.something_else == 15

	mech = src.mechanics()

	assert mech.is_cached('a') and mech.is_cached('b')

	mech.clear_cache()

	try:
		src.something
		assert False
	except Flag:
		pass


def test_mechanics():
	class Tester(ToolKit):
		@gear('a')
		def something(self):
			return 10

		@gear('c')
		def something_else_else(self, a, outside):
			return a + outside

	class Tester2(ToolKit):
		@gear('outside')
		def other(self):
			return 100

	src = Tester()
	src2 = Tester2()

	m = Mechanics(src, src2)

	assert m['a'] == 10
	assert m['c'] == 110
	assert m['outside'] == 100



def test_ref():
	class Tester(ToolKit):
		@gear('a')
		def something(self):
			return 10

	class Tester2(Structured):
		ref = gear('a')

		@gear('b')
		def other(self, a):
			return a + 5

		@gear('c')
		def other2(self):
			return self.ref + 6

	src = Tester()
	src2 = Tester2()

	m = Mechanics(src, src2)
	# src.mechanize(m)
	src2.mechanize(m)

	assert src2.ref == 10
	assert m.is_cached('a')
	assert src2.other == 15
	assert m.is_cached('b')
	assert src2.other2 == 16

	m = Mechanics(src2, src)
	# src.mechanize(m)
	src2.mechanize(m)

	assert src2.ref == 10
	assert m.is_cached('a')
	assert src2.other == 15
	assert m.is_cached('b')
	assert src2.other2 == 16



def test_mechanized_context():
	from .. import tool

	class Tester(Structured):
		@gear('a')
		def something(self):
			return 10

		@gear('c')
		def something_else_else(self, a, outside):
			return a + outside

		@tool('a')
		def f(self):
			return -10

	class Tester2(Structured):
		@gear('outside')
		def other(self):
			return 100

		ref = gear('c')

	src = Tester()
	src2 = Tester2()

	ctx = Context(src, src2).mechanize()

	assert ctx['a'] == -10
	assert src2.ref == 110
	assert src.something_else_else == 110
	assert src2.other == 100



def test_gear_failed():
	class Tester(Structured):
		@gear('a')
		def defer(self):
			raise GearFailed

		@gear('c')
		def something_else_else(self, a, outside):
			return a + outside


	class Tester2(Structured):
		@gear('a')
		def something(self):
			return 10

		@gear('outside')
		def other(self):
			return 100

		ref = gear('c') # reference gear - only accessible in a mechanized environment that contains a 'c' gear

	src = Tester()
	src2 = Tester2()

	try:
		src.defer
		assert False # since the only known gear failed
	except GrabError: # TODO: maybe capture/replace GrabError to make explicit that grabbing a *gear* failed
		pass

	ctx = Context(src, src2).mechanize() # mechanize syncs gears across members

	assert src.defer == 10
	assert src2.ref == 110
	assert src.something_else_else == 110
	assert src2.other == 100


# TODO: test gears with inheritance (should be no different than tools)


def test_gang_gears():
	class Tester(Structured):
		@tool('out')
		def f(self, in1, in2):
			return in1 - in2

		@gear('out')
		def g(self, in1, in2):
			return in1 + in2

		@gear('x')
		def h(self):
			return 299

		@gear('y')
		def i(self, x):
			return x + 1

		@gear('z')
		def j(self):
			return 4

	class Tester2(Structured):
		@gear('a')
		def f(self, y):
			return y + -100

	obj = Tester()
	obj2 = Tester2()

	ctx = Context(obj, obj2).mechanize()

	mech = Mechanism(obj, internal={'x': 'out'}, external={'x': 'in1', 'z': 'in2', 'y': 'z'},
					 insulated=False, exclusive=False)

	ctx.include(mech)

	assert obj.g == 303
	assert obj.h == 299
	assert obj.i == 300
	# note that when debugging this may appear to be 4 due to caching (since the debugger automatically gets properties)
	assert obj.j == 304
	assert obj2.f == 200


