from .imports import *
from .abstract import *
from .contexts import *
from .kits import *


class AbstractDecision(AbstractTool):
	def choices(self) -> Iterator[Any]:
		raise NotImplementedError


	def grab_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		raise NotImplementedError


	def sample(self, ctx):
		raise NotImplementedError
	pass



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


class TestDecider(Cached, Context, TestKit, AbsractDecider):
	def tools(self, gizmo: Optional[str] = None) -> Iterator[AbstractTool]:
		if gizmo is None:
			yield from filter_duplicates(chain.from_iterable(map(reversed, self._tools_table.values())))
		else:
			if gizmo not in self._tools_table:
				raise self._MissingGizmoError(gizmo)
			yield from reversed(self._tools_table[gizmo])


	class _Recorder(Cached, Context):
		def __init__(self, parent: AbstractContext, target: str,
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


		# def grab_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		# 	if self._snapshot is not None and ctx is not self._snapshot:
		# 		return self._snapshot.grab_from(ctx, gizmo)
		# 	return super().grab_from(ctx, gizmo)


		def __iter__(self):
			return self


		def grab_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
			if not self._recording and self._follower is not None:
				return self._follower.grab_from(ctx, gizmo)

			out = super().grab_from(self, gizmo)

			return out


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
		return self._Recorder(self, target, self._tools_table[target])

	def spawn_gizmo(self, target: str) -> Iterable[Any]:
		return self._Recorder(self, target, self._tools_table[target])


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




