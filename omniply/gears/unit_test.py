from .imports import *
from .op import ToolKit, gear, Mechanics, Mechanized



def test_gears():

	class Tester(ToolKit):
		@gear('a')
		def something(self):
			return 10

		@gear('b')
		def something_else(self, a):
			return a + 10

	src = Tester()

	assert src.something == 10
	assert src.something_else == 20


def test_synced():
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

	class Tester2(ToolKit):
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
	src.mechanize(m)
	src2.mechanize(m)

	assert src2.ref == 10
	assert m.is_cached('a')
	assert src2.other == 15
	assert m.is_cached('b')
	assert src2.other2 == 16


	m = Mechanics(src2, src)
	src.mechanize(m)
	src2.mechanize(m)

	assert src2.ref == 10
	assert m.is_cached('a')
	assert src2.other == 15
	assert m.is_cached('b')
	assert src2.other2 == 16




