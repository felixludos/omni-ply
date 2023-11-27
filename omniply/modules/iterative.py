
from collections import OrderedDict
# import torch
# from torch import nn
from omnibelt import agnostic, unspecified_argument#, mix_into
# from .. import util

from ..parameters import submodule, Structured
from ..features import Prepared

from .abstract import AbstractModel, AbstractTrainableModel, AbstractTrainer
from .simple import Evaluatable



class Trainer(Structured, AbstractTrainer):
	model = submodule(builder='model')

	def __init__(self, model=None, **kwargs):
		super().__init__(model=model, **kwargs)
		self.model = model
		self._num_iter = 0


	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)
		self.model.prepare(*args, **kwargs)


	def loop(self, source, **kwargs):
		self.loader = source.get_iterator(**kwargs)
		for batch in self.loader:
			info = self.create_step_container(source=batch, **kwargs)
			yield info


	def create_step_container(self, *args, **kwargs):
		return self.model.create_step_container(*args, **kwargs)


	def fit(self, source, **kwargs):
		self.prepare(source=source)
		info = None
		for batch in self.loop(source, **kwargs):
			info = self.step(batch)
		return self.finish_fit(info)


	def evaluate(self, source, **kwargs):
		info = self.model.evaluate(source, **kwargs)
		return self.finish_evaluate(info)


	def step(self, info):
		out = self.model.step(info)
		self._num_iter += 1
		return out



class TrainableModel(Evaluatable, Structured, AbstractTrainableModel):
	_Trainer = Trainer



# class Loggable(Model): # TODO: this should be in the trainer! the Model just has a function
# # 	def __init__(self, stats=None, **kwargs):
# # 		if stats is None:
# # 			stats = self.Statistics()
# # 		super().__init__(**kwargs)
# # 		self._stats = stats
# #
# #
# # 	class Statistics:
# # 		def mete(self, info, **kwargs):
# # 			raise NotImplementedError
# #
# #
# # 	# def register_stats(self, *stats):
# # 	# 	for stat in stats:
# # 	# 		self._stats.append(stat)
# # 	# 	# for name in names:
# # 	# 	# 	self._stats[name] = self.Statistic(name)
# # 	# 	# for name, stat in stats.items():
# # 	# 	# 	if not isinstance(stat, self.Statistic):
# # 	# 	# 		print(f'WARNING: stat {name} should subclass {self.Statistic.__name__}')
# # 	# 	# 	self._stats[name] = stat
# #
# #
# 	def log(self, info, **kwargs):
# 		pass
# 		# self._stats.mete(info, **kwargs)




# Types of Models





