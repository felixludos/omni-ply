from .imports import *
from .abstract import *
from .contexts import *
from .kits import *


class AbstractCrawler(AbstractContext):
	def __init__(self, source = None):
		super().__init__()
		self._source = source
		self._crawl_stack = []
		self._decisions = []
		self._base = {}
		self._current = None

	_StackEntry = namedtuple('_StackEntry', 'decision gizmo remaining')


	def sub(self, base) -> Iterator[Any]:
		return self._SubCrawler(self, base=base)


	class _SubCrawler(Cached):
		def __init__(self, owner, base=None):
			if base is None:
				base = {}
			super().__init__()
			self.owner = owner
			self.update(base)

		def select(self, decision: 'AbstractDecision', gizmo: str) -> Any:
			return self.owner.select(decision, gizmo)

		def grab_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
			try:
				return super().grab_from(ctx, gizmo)
			except ToolFailedError:
				return self.owner.grab_from(ctx, gizmo)


	def __iter__(self):
		return self


	def __next__(self):
		if not len(self._crawl_stack):
			raise StopIteration

		self._current = None

		frame = self._crawl_stack.pop()

		try:
			value = next(frame.remaining)
		except StopIteration:
			if frame.gizmo in self._base:
				del self._base[frame.gizmo]
			return self.__next__()
		else:
			self._base[frame.gizmo] = value
			self._current = self._SubCrawler(self._base)
			return self._current


	def select(self, decision: 'AbstractDecision', gizmo: str) -> Any:
		if len(self._crawl_stack) > 0:
			assert all(entry.gizmo != gizmo for entry in self._crawl_stack), 'recursive crawl detected'

		generator = decision.choices(gizmo)
		pick = next(generator)
		self._crawl_stack.append(self._StackEntry(decision, gizmo, generator))
		return pick


	def grab_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		if self._current is not None and ctx is not self._current:
			return self._current.grab_from(self._current, gizmo) # traceless delegation to current
		return self._source.grab_from(ctx, gizmo) # traceless delegation to owner

	# def crawl(self, decision: 'AbstractDecision', gizmo: str) -> Iterator[Any]:
	# 	return self._CrawlMonitor(self, decision, gizmo)


class SimpleCrawler(AbstractCrawler):



	pass



class AbstractDecision(AbstractTool):
	def choices(self, gizmo: str) -> Iterator[Any]:
		raise NotImplementedError


	def choose(self, ctx, gizmo: str):
		return ctx.select(self, gizmo)


	def grab_from(self, ctx: Optional['AbstractCrawler'], gizmo: str) -> Any:
		return ctx.select(self, gizmo)






class AbsractDecider(AbstractContext):

	def spawn(self, gizmo: str) -> Iterator[Any]:





		raise NotImplementedError





	pass



class ChoiceExpander:
	def __init__(self, fn, choices):
		self.fn = fn
		self.choices = choices
	
	def __iter__(self):
		return self

	def __next__(self):
		parents = {}
		choices = {key: choice for key, choice in parents.items() if isinstance(choice, AbstractDecision)}




		raise NotImplementedError



class SimpleDecision(AbstractDecision):
	def __init__(self, gizmo: str, choices: Iterable[Any] = ()):
		super().__init__()
		self._choices = choices
		self._gizmo = gizmo


	def gizmos(self) -> Iterator[str]:
		yield self._gizmo


	def __len__(self):
		return len(self._choices)


	def choices(self):
		yield from self._choices



class TestKit(LoopyKit, MutableKit):
	def __init__(self, *tools: AbstractTool, **kwargs):
		super().__init__(**kwargs)
		self.include(*tools)



class Example(AbstractTool):
	def grab_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		a = ctx['a']
		b = ctx['b']
		return a + b


class DynamicProduct:
	def add(self, itr):

		pass


class TestDecider(Cached, Context, TestKit, AbstractCrawler):
	def tools(self, gizmo: Optional[str] = None) -> Iterator[AbstractTool]:
		if gizmo is None:
			yield from filter_duplicates(chain.from_iterable(map(reversed, self._tools_table.values())))
		else:
			if gizmo not in self._tools_table:
				raise self._MissingGizmoError(gizmo)
			yield from reversed(self._tools_table[gizmo])


	class _Crawler(Cached, Context):
		def __init__(self, parent: Cached, target: str,
					 sources: Optional[Dict[str, AbstractDecision]] = None):
			if sources is None:
				sources = {}
			super().__init__()
			self._recording = True
			self._parent = parent
			self._target = target
			self._sources = sources
			self._state = {}
			self._follower = None


		def cached(self) -> Iterator[str]:
			yield from self._parent.cached()
			yield from super().cached()


		def __iter__(self):
			return self


		def _take_snapshot(self, old: AbstractContext, gizmo: str):
			return type(self)(self, gizmo)


		def grab_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
			if not self._recording:
				if self._follower is None:
					if not self.is_cached(gizmo):
						return super().grab_from(self._take_snapshot(ctx, gizmo), gizmo)
				elif ctx is not self._follower:
					return self._follower.grab_from(ctx, gizmo)

			out = self._parent.grab_from(self, gizmo)
			if gizmo == self._target:
				self._recording = False
			return out


		def generate_target(self):
			if len(self.options):
				decision = self.options.pop()




			pass



		def __next__(self):
			try:
				if self._follower is not None:
					return next(self._follower)
			except StopIteration:
				self._follower = None

			for gizmo, choices in self._sources.items():
				if gizmo not in self:
					self[gizmo] = next(choices)
			if self._target in self:
				del self[self._target]
			self[self._target] = next(self._choices)
			return self[self._target]


	def spawn(self, target: str) -> Iterable[Any]:
		return self._Crawler(self, target)


	def spawn_gizmo(self, target: str) -> Iterable[Any]:
		for ctx in self.spawn(target):
			yield ctx[target]


def test_decisions():

	dec = SimpleDecision('simple', choices=[1, 2, 3])

	ctx = TestDecider(dec)

	gz = list(ctx.gizmos())
	assert gz == ['simple']

	itr = ctx.spawn('simple')

	first = next(itr)
	assert first == 1

	rest = list(itr)
	assert rest == [2, 3]



	pass




