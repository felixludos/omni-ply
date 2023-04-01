from ..features.containers import SourceContainer, ScoreContainer
from ..parameters import Structured

from .abstract import AbstractFitable, AbstractEvaluatable, AbstractModel



# class Resultable(AbstractResultable):
# 	class DataContainer(SourceContainer, ScoreContainer):
# 		pass



class Evaluatable(AbstractEvaluatable):
	def create_eval_container(self, *args, **kwargs):
		return self.create_container(*args, **kwargs)


	def evaluate(self, source, **kwargs):
		if not self.is_ready: # no auto prepare
			raise self.NotReady
		info = self.create_eval_container(source=source, **kwargs)
		return self._evaluate(info)


	def _evaluate(self, info):
		raise NotImplementedError



class Fitable(AbstractFitable, AbstractEvaluatable):
	def create_fit_container(self, *args, **kwargs):
		return self.create_container(*args, **kwargs)


	def fit(self, source, **kwargs):
		self.prepare(source)
		info = self.create_fit_container(source=source, **kwargs)
		return self._fit(info)


	def _fit(self, info):
		raise NotImplementedError



class SimpleModel(Fitable, Evaluatable, Structured, AbstractModel):
	pass










