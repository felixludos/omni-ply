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


class AbstractDecision(AbstractTool):
	def choices(self, gizmo: str) -> Iterator[Any]:
		raise NotImplementedError



class SimpleCrawler(AbstractMogul): # TODO: include all options if there are multiple vendors!
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._current = None
		self._crawl_stack = OrderedDict()
		self._crawl_vendors = {}
		self._base = {}

	_StackEntry = namedtuple('_StackEntry', 'gizmo decision remaining')
	_SubCrawler = SimpleFrame
	_SubDecision = AbstractDecision

	def _create_frame(self) -> Iterator[Any]:
		return self._SubCrawler(self, base=self._base)


	def _crawler(self, ctx, gizmo):
		for vendor in self._vendors(gizmo):
			try:
				if isinstance(vendor, self._SubDecision):
					yield from vendor.choices(gizmo)
				else:
					yield vendor.grab_from(ctx, gizmo)
			except ToolFailedError:
				pass
			else:
				return # after the first success, we're done

	def grab_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		if not isinstance(ctx, self._SubCrawler):
			return super().grab_from(ctx, gizmo)

		

		for vendor in self._vendors(gizmo):
			try:
				return vendor.grab_from(ctx, gizmo)
			except ToolFailedError:
				pass


		return ctx[gizmo]


	def _crawl(self):
		gizmo, remaining = self._crawl_stack.popitem()

		try:
			value = next(remaining)
		except StopIteration:
			if gizmo in self._base:
				del self._base[gizmo]
			return self.__next__()
		else:
			self._base[gizmo] = value
			self._current = self._create_frame()
			self._crawl_stack[gizmo] = remaining
			return self._current

	def __next__(self):
		if not len(self._crawl_stack):
			raise StopIteration
		return self._crawl()

	@property
	def current(self):
		if self._current is None:
			self._current = self._create_frame()
		return self._current

	def grab_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		if not isinstance(ctx, self._SubCrawler):
			return self.current.grab_from(self.current, gizmo) # traceless delegation to current

		# current frame has not yet loaded this gizmo - it must be grabbed for real

		if gizmo in self._crawl_stack: # can only happen if gizmo is loopy
			return self._base[gizmo]


		if gizmo not in self._crawl_stack:
			self._crawl_stack[gizmo] = self._crawler(ctx, gizmo)
		return self._crawl()[gizmo]



		if self._source is None:
			return super().grab_from(ctx, gizmo)
		return self._source.grab_from(ctx, gizmo) # traceless delegation to owner



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





