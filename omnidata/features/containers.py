
from collections import OrderedDict#, Mapping
# import torch
from omnibelt import agnostic, unspecified_argument

from .hardware import Device
from .random import Seeded


class AbstractContainer:#(Mapping):
	pass



class Container(OrderedDict, AbstractContainer): # TODO: instead of inheriting from OrderedDict use Mapping (maybe?)
							  # http://www.kr41.net/2016/03-23-dont_inherit_python_builtin_dict_type.html
	def _find_missing(self, key):
		raise KeyError(key)


	class _missing: # flag for missing items
		pass


	def merge(self, info: 'Container'):
		self.update(info)


	def __getitem__(self, item):
		try:
			return super().__getitem__(item)
		except KeyError:
			return self._find_missing(item)
			# self[item] = val
			# return val


	def __str__(self):
		entries = ', '.join(self.keys())
		return f'{self.__class__.__name__}({entries})'


	def __repr__(self):
		return str(self)



class DevicedContainer(Device, Container):
	def _to(self, device, **kwargs):
		for key, val in self.items():
			if isinstance(val, (Device, torch.Tensor)):
				self[key] = val.to(device)



class SourceContainer(Container):
	def __init__(self, source=None, **kwargs):
		super().__init__(**kwargs)
		self.source = source


	def merge(self, info: 'Container'):
		if isinstance(info, SourceContainer) and info.source is not None:
			self.source = info.source
		return super().merge(info)


	def new_source(self, source):
		self.clear()
		self.source = source


	def _load_missing(self, key):
		return self.source[key]


	def _find_missing(self, key):
		if self.source is not None:
			self[key] = self._load_missing(key) # load and cache
			return self[key]
		return super()._find_missing(key)



class ScoreContainer(Container):
	_score_key = None
	def __init__(self, *, score_key=None, **kwargs):
		super().__init__(**kwargs)
		if score_key is not None:
			self._score_key = score_key


	def merge(self, info: 'Container'):
		if isinstance(info, ScoreContainer) and info._score_key is not None:
			self._score_key = info._score_key
		return super().merge(info)


	class NoScoreKeyError(Exception):
		pass


	def _find_missing(self, key, **kwargs):
		if key == 'score':
			if self._score_key is None:
				raise self.NoScoreKeyError
			return self[self._score_key]
		return super()._find_missing(key)


	def __contains__(self, item):
		return super().__contains__(item) or (item == 'score' and super().__contains__(self._score_key))









