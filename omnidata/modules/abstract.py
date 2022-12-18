from omnibelt import agnostic

from ..features import Prepared
from ..parameters.abstract import AbstractBuilder


class AbstractResultable(Prepared):
	DataContainer = None
	@agnostic
	def create_container(self, *args, **kwargs):
		return self.DataContainer(*args, **kwargs)



class AbstractEvaluatable(AbstractResultable):
	@staticmethod
	def evaluate(source, **kwargs):
		raise NotImplementedError



class AbstractFitable(AbstractResultable):
	@staticmethod
	def fit(source, **kwargs):
		raise NotImplementedError



class AbstractTrainable(AbstractFitable):
	# def create_step_results_container(self, *args, **kwargs):
	# 	return self.create_results_container(*args, **kwargs)

	Trainer = None
	def fit(self, source, **kwargs):
		self.prepare(source)
		trainer = self.Trainer(self)
		return trainer.fit(source=source, **kwargs)

	@staticmethod
	def step(info):
		raise NotImplementedError



class AbstractModel(AbstractBuilder, AbstractFitable, AbstractEvaluatable):
	pass


class AbstractTrainableModel(AbstractModel, AbstractTrainable):
	pass


class AbstractTrainer(AbstractBuilder, AbstractFitable, AbstractEvaluatable):
	def __init__(self, model, **kwargs):
		super().__init__(**kwargs)


	def loop(self, source, **kwargs):
		raise NotImplementedError


	def create_step_container(self, *args, **kwargs):
		raise NotImplementedError


	def step(self, info):
		raise NotImplementedError


	def finish_fit(self, info):
		return info


	def finish_evaluate(self, info):
		return info





