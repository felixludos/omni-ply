from omnibelt import agnostic

from ..features import Prepared
from ..parameters.abstract import AbstractBuilder



class AbstractEvaluatable:
	@staticmethod
	def evaluate(source, **kwargs):
		raise NotImplementedError



class AbstractFitable:
	@staticmethod
	def fit(source, **kwargs):
		raise NotImplementedError



class AbstractTrainable(AbstractFitable, Prepared):
	_Trainer = None
	def fit(self, source, **kwargs):
		self.prepare(source)
		trainer = self._Trainer(self)
		return trainer.fit(source=source, **kwargs)


	def step(self, batch):
		pass



class AbstractModel(AbstractFitable, AbstractEvaluatable):
	pass



class AbstractTrainableModel(AbstractModel, AbstractTrainable):
	pass



class AbstractTrainer(AbstractFitable, AbstractEvaluatable):
	def __init__(self, model=None, **kwargs):
		super().__init__(**kwargs)
		if model is not None:
			self.set_model(model)


	def set_model(self, model):
		raise NotImplementedError


	def loop(self, source, **kwargs):
		raise NotImplementedError


	def step(self, batch):
		raise NotImplementedError





