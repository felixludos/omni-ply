
from collections import OrderedDict
import torch
from torch import nn
from omnibelt import agnostic, unspecified_argument#, mix_into
# from .. import util
from . import abstract
from .features import Seeded, Prepared
from .hyperparameters import hparam
from .parameterized import inherit_hparams
from .machines import machine
from .top import Parameterized
from .base import Function, Container


# class ModelBuilder:
# 	@agnosticmethod
# 	def build(self, dataset):
# 		raise NotImplementedError



# class ModelBuilder:
# 	def __init__(self, **kwargs):
# 		self.update(**kwargs)
#
#
# 	def update(self, **kwargs):
# 		self.__dict__.update(kwargs)
#
#
# 	def __call__(self, **kwargs):
# 		self.update(**kwargs)
# 		return self.build()
#
#
# 	class MissingKwargsError(KeyError):
# 		def __init__(self, *keys):
# 			super().__init__(', '.join(keys))
# 			self.keys = keys
#
#
# 	def build(self):
# 		raise NotImplementedError



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



# class Buildable(ModuleParametrized): # TODO: unify building and hparams - they should be shared
# 	# def __init_subclass__(cls, builder=None, **kwargs):
# 	# 	super().__init_subclass__(**kwargs)
# 	# 	if builder is None:
# 	# 		builder = cls.Builder(cls)
# 	# 	cls.builder = builder
#
# 	# _my_build_settings = {} # in a sub-class of Buildable
#
#
# 	@agnosticmethod
# 	def get_builder(self, cls=None, **kwargs):
# 		if cls is None:
# 			cls = self if isinstance(self, type) else self.__class__
# 		return self.Builder(cls=cls, **kwargs)
#
#
# 	class Builder(ModelBuilder):
# 		def __init__(self, cls=None, **kwargs):
# 			super().__init__(**kwargs)
# 			if cls is None:
# 				raise self.MissingSourceClassError
# 			self.update(**{key:getattr(cls, key) for key in cls.iterate_hparams()})
# 			self.cls = cls
#
#
# 		class MissingSourceClassError(Exception):
# 			def __init__(self):
# 				super().__init__('You cannot instantiate a builder without a source class '
# 				                 '(use cls.builder instead)')
#
#
# 		def build(self, kwargs=None):
# 			if kwargs is None:
# 				kwargs = self.__dict__.copy()
# 				del kwargs['cls']
# 			return self.cls(**kwargs)



class Computable(Parameterized, Resultable):
	@agnostic
	def compute(self, source=None, **kwargs):
		info = self.create_results_container(source=source, **kwargs)
		self.info = info # TODO: clean up maybe?
		out = self._compute(info)
		if hasattr(self, 'info'):
			del self.info
		return out


	@staticmethod
	def _compute(info):
		raise NotImplementedError



class Fitable(Resultable):
	def fit(self, source, **kwargs):
		raise NotImplementedError


	def evaluate(self, source, **kwargs):
		raise NotImplementedError



class Model(#Buildable,
            Parameterized, Fitable, Prepared):
	def _prepare(self, source=None, **kwargs):
		pass


	@agnostic
	def create_fit_results_container(self, **kwargs):
		return self.create_results_container(**kwargs)


	def fit(self, source, **kwargs):
		self.prepare(source)
		info = self.create_fit_results_container(source=source, **kwargs)
		return self._fit(info)


	@staticmethod
	def _fit(info):
		raise NotImplementedError


	def evaluate(self, source, **kwargs):
		if not self.is_ready:
			raise self.NotReady
		info = self.create_results_container(source=source, **kwargs)
		return self._evaluate(info)


	@staticmethod
	def _evaluate(info):
		raise NotImplementedError


# TODO: hparams that should be extracted from the config should be specified with a decorator


class Trainer(Parameterized, Fitable, Prepared):
	# model = hparam(None)
	model = machine(type=Model)

	def __init__(self, model, source=None, **kwargs):
		super().__init__(**kwargs)
		self.source = source
		self.model = model

		self._num_iter = 0


	def loop(self, source, **kwargs):
		self.loader = source.get_iterator(**kwargs)
		for batch in self.loader:
			yield batch


	@agnostic
	def create_step_results_container(self, **kwargs):
		return self.model.create_step_results_container(**kwargs)


	def _prepare(self, source=None, **kwargs):
		pass


	def fit(self, source=None, **kwargs):
		if source is None:
			source = self.source
		self.prepare(source=source)
		for batch in self.loop(source, **kwargs):
			info = self.step(batch)
		return self.finish_fit(info)


	def evaluate(self, source=None, **kwargs):
		if source is None:
			source = self.source
		info = self.model.evaluate(source, **kwargs)
		return self.finish_evaluate(info)


	def step(self, source, **kwargs):
		info = self.create_step_results_container(source=source, **kwargs)
		out = self.model.step(info)
		self._num_iter += 1
		return out


	def finish_fit(self, info):
		return info


	def finish_evaluate(self, info):
		return info



class TrainableModel(Model):
	@agnostic
	def create_step_results_container(self, **kwargs):
		return self.create_results_container(**kwargs)


	Trainer = Trainer
	@agnostic
	def fit(self, source, info=None, **kwargs):
		assert info is None, 'cant merge info (yet)' # TODO
		trainer = self.Trainer(self)
		return trainer.fit(source=source, **kwargs)


	@agnostic
	def step(self, info, **kwargs):
		self._step(info, **kwargs)
		return info


	@agnostic
	def _step(self, info):
		raise NotImplementedError


	@agnostic
	def eval_step(self, info, **kwargs):
		self._step(info, **kwargs)
		return info



class Loggable(Model): # TODO: this should be in the trainer! the Model just has a function
# 	def __init__(self, stats=None, **kwargs):
# 		if stats is None:
# 			stats = self.Statistics()
# 		super().__init__(**kwargs)
# 		self._stats = stats
#
#
# 	class Statistics:
# 		def mete(self, info, **kwargs):
# 			raise NotImplementedError
#
#
# 	# def register_stats(self, *stats):
# 	# 	for stat in stats:
# 	# 		self._stats.append(stat)
# 	# 	# for name in names:
# 	# 	# 	self._stats[name] = self.Statistic(name)
# 	# 	# for name, stat in stats.items():
# 	# 	# 	if not isinstance(stat, self.Statistic):
# 	# 	# 		print(f'WARNING: stat {name} should subclass {self.Statistic.__name__}')
# 	# 	# 	self._stats[name] = stat
#
#
	def log(self, info, **kwargs):
		pass
		# self._stats.mete(info, **kwargs)




# Types of Models





