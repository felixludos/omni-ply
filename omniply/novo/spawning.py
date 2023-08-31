from .contexts import *
from .kits import *


class AbstractMogul(AbstractGig):
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


class SimpleFrame(Cached, Gig, MutableKit, AbstractCrawler):
	def __init__(self, owner, base=None):
		if base is None:
			base = {}
		super().__init__()
		self._owner = owner
		# self.update(base)
		self._frame = base # choices that were made

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
		if gizmo in self._frame:
			return self._frame[gizmo]
		value = self._owner.select(decision, gizmo)
		self._frame[gizmo] = value
		return value

	def _grab(self, gizmo: str) -> Any:
		return self._owner.grab_from(self, gizmo)



class AbstractDecision(AbstractGadget):
	def choices(self, gizmo: str) -> Iterator[Any]:
		raise NotImplementedError



class SimpleCrawler(AbstractCrawler): # TODO: include all options if there are multiple vendors!
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._current = None
		self._crawl_stack = OrderedDict()
		self._current_base = {}

	# _StackEntry = namedtuple('_StackEntry', 'gizmo decision remaining')
	_SubCrawler = SimpleFrame
	_SubDecision = AbstractDecision

	def select(self, decision: 'AbstractDecision', gizmo: str) -> Any:
		assert isinstance(decision, self._SubDecision), f'Expected {self._SubDecision}, got {decision}'
		if gizmo in self._current_base: # (past) frames lazily get missing base values from current -> can be tricky
			return self._current_base[gizmo]
		assert gizmo not in self._crawl_stack, f'Gizmo {gizmo} already selected'
		options = decision.choices(gizmo)
		self._crawl_stack[gizmo] = options
		return self._crawl_step()

	def _crawl_step(self):
		assert len(self._crawl_stack) > 0, 'Nothing to crawl'

		gizmo, remaining = self._crawl_stack.popitem()
		if gizmo in self._current_base: # removed previous value from cache
			del self._current_base[gizmo]

		value = next(remaining)
		self._current_base[gizmo] = value
		self._crawl_stack[gizmo] = remaining
		return value

	def __next__(self):
		while len(self._crawl_stack) > 0:
			try:
				self._crawl_step()
			except StopIteration:
				pass
			else:
				self._current = self._create_frame()
				return self._current
		raise StopIteration

	def _create_frame(self) -> Iterator[Any]:
		return self._SubCrawler(self, base=self._current_base.copy())

	@property
	def current(self):
		if self._current is None:
			self._current = self._create_frame()
		return self._current

	def grab_from(self, ctx: Optional['AbstractGig'], gizmo: str) -> Any:
		if not isinstance(ctx, self._SubCrawler):# and self._current is not None:
			return self.current.grab_from(self.current, gizmo) # traceless delegation to current
		# current frame has not yet loaded this gizmo - it must be grabbed for real
		return super().grab_from(ctx, gizmo)





