


# Iterable[Context] -> Mogul
# Iterator[Context] -> Guru


from typing import Iterator, Iterable, Union, Any, Self

from .. import AbstractGadget
from ..core import AbstractGame, Context
from ..core.abstract import AbstractMutable
from .simple import DictGadget



class AbstractGuru:
	def gift(self) -> AbstractGame:
		raise NotImplementedError


	def __iter__(self):
		return self


	def __next__(self):
		return self.gift()




class AbstractMogul:
	def guide(self) -> AbstractGuru:
		'''passing a guide will extend'''
		raise NotImplementedError


	def __iter__(self):
		return self.guide()



class AbstractStackableMogul(AbstractMogul):
	def guide(self, guide: AbstractGuru = None) -> AbstractGuru:
		'''passing a guide will extend'''
		raise NotImplementedError



class Generous(AbstractGuru):
	def gift(self) -> AbstractGame:
		value = next(self.genie)
		return self.grant(value)


	def grant(self, base: Any) -> AbstractGame:
		raise NotImplementedError


	@property
	def genie(self) -> Iterator[Any]:
		raise NotImplementedError



class SimpleGuru(Generous):
	def __init__(self, src: Iterable[AbstractGame] | Iterable[int] | int, key: str = 'idx', **kwargs):
		super().__init__(**kwargs)
		self._src = src
		self._itr = None
		self._key = key


	@property
	def genie(self):
		if self._itr is None:
			self._itr = self._geniefy(self._src)
		return self._itr


	def _geniefy(self, src: Iterable[AbstractGame] | Iterable[int] | int):
		if isinstance(src, int):
			src = range(src)
		return iter(src)


	def grant(self, value: AbstractGame | int):
		if isinstance(value, AbstractGame):
			return value
		return Context(DictGadget({self._key: value}))



class MutableGuru(SimpleGuru, AbstractMutable):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._gadgets = []


	def grant(self, value: int) -> AbstractMutable:
		return super().grant(value).extend(self._gadgets)


	def extend(self, gadgets):
		self._gadgets.extend(gadgets)
		return self


	def exclude(self, *gadgets: AbstractGadget) -> Self:
		for gadget in gadgets:
			self._gadgets.remove(gadget)
		return self



class CountableGuru(AbstractGuru):
	def __init__(self, *args, expected: int = None, **kwargs):
		super().__init__(*args, **kwargs)
		self._past = 0
		self._expected = expected

	def gift(self):
		gift = super().gift()
		self._past += 1
		return gift

	def __len__(self):
		return self.total

	@property
	def total(self):
		return self._expected

	@property
	def past(self):
		return self._past

	@property
	def remaining(self):
		if self._expected is not None:
			return self._expected - self._past



class Guru(CountableGuru, MutableGuru):
	def _geniefy(self, src: Iterable[AbstractGame] | Iterable[int] | int):
		if isinstance(src, int):
			self._expected = src
		else:
			try:
				self._expected = len(src)
			except TypeError:
				pass
		return super()._geniefy(src)








