from .recording import Context, Mechanism



def test_recording():

	from ..gaps import tool, ToolKit
	from ...core import GadgetFailed, MissingGadget, GrabError

	class Tester(ToolKit):
		@tool('a')
		def f(self):
			return 10

		@tool('b')
		def g(self, a):
			return a + 10

		@tool('c')
		def h(self, b, d):
			return b - d

	@tool('b')
	def i():
		raise GadgetFailed

	ctx = Context(i, Tester(gap={'a': 'x'}))

	ctx['d'] = 5

	ctx.record()

	assert ctx.grab('c') == 15

	ctx.clear_cache()

	assert ctx.grab('x') == 10
	assert ctx.grab('b') == 20

	try:
		ctx.grab('c') # d is missing
	except GrabError:
		pass

	assert ctx.grab('x') == 10

	report = ctx.report(ret_ctx=True)

	print()

	pretty = ctx.report()
	print(pretty)
	print()



def test_loopy():
	from ...core import tool, ToolKit

	@tool('a')
	def i():
		return 5

	@tool('a')
	def j(a):
		return a - 1

	ctx = Context(j, i)

	ctx.record()

	assert ctx.grab('a') == 4

	report = ctx.report(ret_ctx=True)

	print()

	pretty = ctx.report()
	print(pretty)
	print()



def test_gang_recording():

	from ...core import tool, ToolKit
	from ...core import GadgetFailed, MissingGadget, GrabError

	class Tester(ToolKit):
		@tool('a')
		def f(self):
			return 10

		@tool('b')
		def g(self, a):
			return a + 4

		@tool('c')
		def h(self, a, b):
			return b - a

	src = Tester()
	mech = Mechanism(src, external={'c': 'd'}, internal={'b': 'a'})
	ctx = Context(src, mech)

	print()
	ctx.record()

	assert ctx.grab('c') == 4

	print(ctx.report())

	ctx.clear_cache()
	print()
	ctx.record()

	assert ctx.grab('d') == 0

	print(ctx.report())



def test_double_gang_recording():
	from ...core import tool, ToolKit
	from ..simple import DictGadget

	class Tester1(ToolKit):
		@tool('hidden')
		def f(self):
			return 5

		@tool('a')
		def g(self, x):
			return 50 - x

	class Tester2(ToolKit):
		@tool('b')
		def h(self):
			return 100

		@tool('c')
		def h(self, b):
			return b - 10

	mech1 = Mechanism(Tester1(), external={'a': 'y', 'hidden': 'b'}, internal={'x': 'b'})
	mech2 = Mechanism(Tester2(), external={'c': 'out'}, internal={'b': 'y'})
	ctx = Context(mech1, mech2)

	print()
	ctx.record()

	assert list(ctx.gizmos()) == ['b', 'y', 'out']

	assert ctx.grab('out') == 35

	print(ctx.report())

	ctx.clear_cache()
	print()


