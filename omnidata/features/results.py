
from collections import OrderedDict, Mapping
import torch
from omnibelt import agnostic, unspecified_argument

from .hardware import Device
from .random import Seeded


class AbstractContainer(Mapping):
	pass


class Container(AbstractContainer, OrderedDict): # TODO: instead of inheriting from OrderedDict use Mapping (maybe?)
							  # http://www.kr41.net/2016/03-23-dont_inherit_python_builtin_dict_type.html
	def _find_missing(self, key):
		raise KeyError(key)


	class _missing: # flag for missing items
		pass


	def __getitem__(self, item):
		try:
			return super().__getitem__(item)
		except KeyError:
			return self._find_missing(item)
			# self[item] = val
			# return val


	# def export(self):
	# 	raise NotImplementedError


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



class Resultable:
	seed = None
	score_key = None

	class ResultsContainer(Seeded, Container):
		def __init__(self, source=None, score_key=None, **kwargs):
			super().__init__(**kwargs)
			self.source = source
			self._score_key = score_key


		def new_source(self, source):
			self.clear()
			self.source = source


		class NoScoreKeyError(Exception):
			pass


		def merge_results(self, info):
			self.update(info)


		def _load_missing(self, key, **kwargs):
			return self.source.get(key, **kwargs)


		def _find_missing(self, key, **kwargs):
			if key == 'score':
				if self._score_key is None:
					raise self.NoScoreKeyError
				return self[self._score_key]
			if self.source is not None:
				self[key] = self._load_missing(key, **kwargs) # load and cache
				return self[key]
			return super()._find_missing(key)


		def __contains__(self, item):
			return super().__contains__(item) or (item == 'score' and super().__contains__(self._score_key))


	@agnostic
	def heavy_results(self):
		return set()


	@agnostic
	def score_names(self):
		return set()


	@agnostic
	def filter_heavy(self, info):
		heavy = self.heavy_results()
		return {key:val for key, val in info.items() if key not in heavy}


	@agnostic
	def _integrate_results(self, info, **kwargs):
		raise NotImplementedError # TODO
		if not isinstance(info, self.ResultsContainer):
			new = mix_into(self.ResultsContainer, info)
		# TODO: run __init__ of new super classes with **kwargs
		return new


	@agnostic
	def create_results_container(self, info=None, score_key=None, seed=unspecified_argument, **kwargs):
		if score_key is None:
			score_key = self.score_key
		if seed is unspecified_argument:
			seed = self.seed
		if info is not None:
			return self._integrate_results(info, score_key=score_key, seed=seed, **kwargs)
		return self.ResultsContainer(score_key=score_key, **kwargs)









