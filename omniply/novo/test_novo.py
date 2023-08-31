from .imports import *

from .tools import *
from .kits import *
from .behaviors import *
from .contexts import *
from .quirks import *
from .quirky import *
from .spawning import *
from .tools import ToolDecorator, AutoToolDecorator

# added by codespaces


class tool(AutoToolDecorator):
	from_context = ToolDecorator



class TestKit(LoopyKit, MutableKit):
	def __init__(self, *tools: AbstractGadget, **kwargs):
		super().__init__(**kwargs)
		self.include(*tools)



class TestCraftyKitBase(CraftyKit):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._process_crafts()



class TestContext(Cached, Gig, TestKit):#, Kit, AbstractContext):
	def tools(self, gizmo: Optional[str] = None) -> Iterator[AbstractGadget]:
		if gizmo is None:
			yield from filter_duplicates(chain.from_iterable(map(reversed, self._tools_table.values())))
		else:
			if gizmo not in self._tools_table:
				raise self._MissingGizmoError(gizmo)
			yield from reversed(self._tools_table[gizmo])



def test_tool():
	@tool('a')
	def f(x):
		return x + 1

	assert f(1) == 2

	@tool('b')
	def g(x, y, z):
		return x + y + z



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



class TestCraftyKit(MutableKit, TestCraftyKitBase):
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



class TestCraftyKit2(TestCraftyKit): # by default inherits all tools from the parents
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

	def g(self, x): # overriding a tool (this will be registered, rather than the super method)
		# use with caution - it's recommended to use clear naming for the function
		return super().g(x, x) # super method can be called as usual



def test_crafty_kit_inheritance():

	assert TestCraftyKit2.f(1) == 2
	assert TestCraftyKit2.h(1) == 3

	kit = TestCraftyKit2()
	assert kit.f(1) == 2
	assert kit.g(2) == 4
	assert kit.h(1) == 3
	assert kit.check() == 40
	assert kit.get_x() == 100
	assert kit.change_y(1) == 11

	ctx = TestContext(kit)

	assert list(ctx.gizmos()) == ['y', 'z', 'w', 'x']

	assert ctx['x'] == 100
	assert ctx['y'] == 111
	assert ctx['z'] == 200
	assert ctx['w'] == 202

	ctx.clear_cache()

	@tool('z')
	def new_z():
		return 1000

	ctx.include(new_z)

	assert 'x' not in ctx.cached()
	assert ctx['y'] == 111
	assert 'x' in ctx.cached()
	assert ctx['x'] == 100

	assert ctx['z'] == 1000
	assert ctx['w'] == 1002



class LambdaTool(AbstractGadget):
	def __init__(self, fn, inp='input', out='output', **kwargs):
		if isinstance(inp, str):
			inp = [inp]
		super().__init__(**kwargs)
		self.fn = fn
		self.input_keys = inp
		self.output_key = out


	def __call__(self, *args, **kwargs):
		return self.fn(*args, **kwargs)


	def gizmos(self) -> Iterator[str]:
		yield self.output_key


	def grab_from(self, ctx: Optional[AbstractGig], gizmo: str) -> Any:
		if gizmo != self.output_key:
			raise GadgetFailedError(gizmo)
		# inputs = [ctx[g] for g in self.input_keys]
		inputs = [ctx.grab_from(ctx, g) for g in self.input_keys]
		return self.fn(*inputs)



class TestData(TestCraftyKitBase):
	@tool('data')
	def get_data(self):
		return 1, 1

	@tool('x')
	def get_x(self, data):
		return data[0]

	@tool('y_true')
	def get_y_true(self, data):
		return data[1]



class trait(AppliedTrait, SimpleQuirk):
	pass



class SuperModule(TestCraftyKitBase, Capable):
	augmentation = trait(apply={'input': 'x', 'output': 'x'})
	model = trait(apply={'input': 'x', 'output': 'y'})


	@tool('loss')
	@staticmethod
	def loss(y, y_true):
		return (y - y_true) ** 2


# class SuperModule2(SuperModule):
# 	augmentation = trait(apply={'input': 'original', 'output': 'augmented'})
# 	interpolator = trait(apply={'input1': 'original', 'input2': 'augmented', 'output': 'x'})
# 	model = trait(apply={'input': 'augmented', 'output': 'y'})



def test_trait():

	@tool('output')
	def augmentation(input):
		return input + 1

	@tool('output')
	def model(input):
		return input * 2

	sup = SuperModule(augmentation=augmentation, model=model)

	assert list(sup.gizmos()) == ['x', 'y', 'loss']

	ctx = TestContext(sup) # uses loopy getting

	assert list(ctx.gizmos()) == ['x', 'y', 'loss']

	ctx = TestContext(sup, TestData())

	assert ctx['loss'] == 9
	assert ctx['y'] == 4 # not 3, because the augmentation is applied first



class TestCrawler(SimpleCrawler, LoopyKit, MutableKit):
	def spawn(self, gizmo: Optional[str] = None) -> Iterator[Any]:
		if gizmo is not None:
			self.current.grab(gizmo)
		yield self.current
		yield from self

	def spawn_gizmo(self, gizmo: str) -> Iterator[str]:
		yield self[gizmo]
		for element in self:
			yield element[gizmo]



class TestDecision(AbstractDecision):
	def __init__(self, gizmo: str, choices: Iterable[Any] = (), **kwargs):
		if not isinstance(choices, (list, tuple)):
			choices = list(choices)
		super().__init__(**kwargs)
		self._choices = choices
		self._gizmo = gizmo

	def grab_from(self, ctx: Optional['AbstractGig'], gizmo: str) -> Any:
		if isinstance(ctx, AbstractCrawler):
			return ctx.select(self, gizmo)
		return super().grab_from(ctx, gizmo)

	def gizmos(self) -> Iterator[str]:
		yield self._gizmo

	def __len__(self):
		return len(self._choices)

	def choices(self, gizmo: str = None):
		yield from self._choices


def test_decisions():

	dec = TestDecision('simple', choices=[1, 2, 3])

	gz = list(dec.gizmos())
	assert gz == ['simple']

	ctx = TestCrawler().include(dec)

	gz = list(ctx.gizmos())
	assert gz == ['simple']

	x = ctx['simple']
	assert x == 1

	second = next(ctx)
	assert second['simple'] == 2

	rest = list(ctx)
	assert len(rest) == 1
	assert rest[0]['simple'] == 3


def test_tooled_decision():

	dec = TestDecision('chain', choices=[1, 2, 3])

	@tool('chain')
	def negative(chain):
		return -chain

	ctx = TestCrawler().include(negative, dec)

	assert list(ctx.gizmos()) == ['chain']

	itr = ctx.spawn('chain')

	frames = list(itr)
	results = []
	for f in frames:
		results.append(f['chain'])
	assert results == [-1, -2, -3]



def test_multi_decision():
	@tool('c')
	def c(a, b):
		return a + b

	a = TestDecision('a', choices=[10, 20, 30])
	b = TestDecision('b', choices=[1, 2, 3])

	ctx = TestCrawler().include(a, b, c)

	assert list(ctx.gizmos()) == ['a', 'b', 'c']

	itr = ctx.spawn_gizmo('c')

	results = list(itr)
	assert results == [11, 12, 13, 21, 22, 23, 31, 32, 33]







