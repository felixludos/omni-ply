from .imports import *

from .abstract import AbstractMogul, AbstractInnovator



class MogulIterator:
	def __init__(self, mogul: AbstractMogul, stream: Iterator[Any]):
		self.mogul = mogul
		self.stream = stream


	def __iter__(self):
		return self


	def __next__(self):
		item = next(self.stream)
		return self.mogul.announce(item)



class StreamMogul(ToolKit, AbstractMogul):
	_context_type = Context
	_iterator_type = MogulIterator

	def announce(self, item: Any):
		return self._context_type(item).include(self)


	def _generate_stream(self):
		raise NotImplementedError


	def __iter__(self):
		return self._iterator_type(self, self._generate_stream())












