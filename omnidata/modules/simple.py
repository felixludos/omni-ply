from ..features.containers import SourceContainer, ScoreContainer
from ..parameters import Parameterized

from .abstract import AbstractResultable, AbstractFitable, AbstractEvaluatable, AbstractModel



class Resultable(AbstractResultable):
	class DataContainer(SourceContainer, ScoreContainer):
		pass



class Evaluatable(Resultable, AbstractEvaluatable):
	def create_eval_container(self, *args, **kwargs):
		return self.create_container(*args, **kwargs)


	def evaluate(self, source, **kwargs):
		if not self.is_ready: # no auto prepare
			raise self.NotReady
		info = self.create_eval_container(source=source, **kwargs)
		return self._evaluate(info)


	def _evaluate(self, info):
		raise NotImplementedError



class Fitable(Resultable, AbstractFitable, AbstractEvaluatable):
	def create_fit_container(self, *args, **kwargs):
		return self.create_container(*args, **kwargs)


	def fit(self, source, **kwargs):
		self.prepare(source)
		info = self.create_fit_container(source=source, **kwargs)
		return self._fit(info)


	def _fit(self, info):
		raise NotImplementedError



class SimpleModel(Fitable, Evaluatable, Parameterized, AbstractModel):
	pass










