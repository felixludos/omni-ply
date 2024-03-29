from .imports import *

from .abstract import AbstractGuru, AbstractGod


#
# class MogulIterator:
# 	def __init__(self, mogul: AbstractMogul, stream: Iterator[Any]):
# 		self.mogul = mogul
# 		self.stream = stream
#
#
# 	def __iter__(self):
# 		return self
#
#
# 	def __next__(self):
# 		item = next(self.stream)
# 		return self.mogul.announce(item)
#
#
#
# class StreamMogul(ToolKit, AbstractMogul):
# 	_context_type = Context
# 	_iterator_type = MogulIterator
#
# 	def announce(self, item: Any):
# 		return self._context_type(item).include(self)
#
#
# 	def _generate_stream(self):
# 		raise NotImplementedError
#
#
# 	def __iter__(self):
# 		return self._iterator_type(self, self._generate_stream())
#



class GuruBase(AbstractGuru):
	def __init__(self, source: AbstractGod, **kwargs):
		super().__init__(**kwargs)
		self._source = source
		self._content = []


	def extend(self, content: Iterable[AbstractGadget]):
		self._content.extend(content)


	def include(self, *gadgets: AbstractGadget):
		self._content.extend(gadgets)


	def exclude(self, *gadgets: AbstractGadget):
		for gadget in gadgets:
			self._content.remove(gadget)


	def gadgetry(self) -> Iterator[AbstractGadget]:
		yield from self._content


	def __iter__(self):
		return self._source.grant(self)


	def __next__(self):
		return next(self._source.grant(self))








