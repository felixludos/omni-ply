from .imports import *
from .abstract import *
from .contexts import *
from .kits import *


class AbstractMogul(AbstractContext):
	def __iter__(self):
		return self

	def __next__(self):
		raise NotImplementedError

	@property
	def current(self):
		raise NotImplementedError


class AbstractCrawler(AbstractMogul):
	def select(self, decision: 'AbstractDecision', gizmo: str) -> Any:
		raise NotImplementedError


class SimpleFrame(Cached, Context, MutableKit, AbstractMogul):
	def __init__(self, owner, base=None):
		if base is None:
			base = {}
		super().__init__()
		self._owner = owner
		self.update(base)

	@property
	def current(self):
		return self._owner.current

	def __next__(self):
		return next(self._owner)

	def __iter__(self):
		return self._owner

	def gizmos(self) -> Iterator[str]:
		yield from filter_duplicates(super().gizmos(), self._owner.gizmos())

	def select(self, decision: 'AbstractDecision', gizmo: str) -> Any:
		return self._owner.select(decision, gizmo)

	def grab_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		try:
			return super().grab_from(ctx, gizmo)
		except ToolFailedError:
			return self._owner.grab_from(ctx, gizmo)


class SimpleCrawler(AbstractMogul):
	def __init__(self, source = None, **kwargs):
		super().__init__(**kwargs)
		self._current = None
		self._source = source
		self._crawl_stack = []
		self._base = {}

	_StackEntry = namedtuple('_StackEntry', 'decision gizmo remaining')
	_SubCrawler = SimpleFrame

	def sub(self, base: Dict[str, Any] = None) -> Iterator[Any]:
		return self._SubCrawler(self, base=base)

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
			self._current = self.sub(self._base)
			self._crawl_stack.append(frame)
			return self._current

	def select(self, decision: 'AbstractDecision', gizmo: str) -> Any:
		if len(self._crawl_stack) > 0:
			assert all(entry.gizmo != gizmo for entry in self._crawl_stack), 'recursive crawl detected'

		generator = decision.choices(gizmo)
		pick = next(generator)
		self._base[gizmo] = pick
		self._crawl_stack.append(self._StackEntry(decision, gizmo, generator))
		return pick

	@property
	def current(self):
		if self._current is None:
			self._current = self.sub(self._base)
		return self._current

	def grab_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		if ctx is not self.current:
			return self.current.grab_from(self.current, gizmo) # traceless delegation to current
		if self._source is None:
			return super().grab_from(ctx, gizmo)
		return self._source.grab_from(ctx, gizmo) # traceless delegation to owner


class AbstractDecision(AbstractTool):
	def choices(self, gizmo: str) -> Iterator[Any]:
		raise NotImplementedError

	def choose(self, ctx: AbstractContext, gizmo: str) -> Any:
		raise NotImplementedError

	def grab_from(self, ctx: AbstractContext, gizmo: str) -> Any:
		return self.choose(ctx, gizmo)



class SimpleDecision(AbstractDecision):
	def __init__(self, gizmo: str, choices: Iterable[Any] = ()):
		if not isinstance(choices, (list, tuple)):
			choices = list(choices)
		super().__init__()
		self._choices = choices
		self._gizmo = gizmo

	def gizmos(self) -> Iterator[str]:
		yield self._gizmo

	def __len__(self):
		return len(self._choices)

	def choices(self, gizmo: str = None):
		yield from self._choices

	def choose(self, ctx: AbstractCrawler, gizmo: str):
		return ctx.select(self, gizmo)





