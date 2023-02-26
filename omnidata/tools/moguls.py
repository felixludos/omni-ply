# moguls generate contexts

from .abstract import AbstractMogul



class StreamMogul(AbstractMogul):
	def __iter__(self):
		raise NotImplementedError



class LimitMogul(StreamMogul):
	def __len__(self):
		raise NotImplementedError



class SelectionMogul(StreamMogul):
	def __getitem__(self, item):
		raise NotImplementedError













