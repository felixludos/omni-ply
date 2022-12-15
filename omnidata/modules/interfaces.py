
from ..features import Resultable


class Evaluatable(Resultable):
	def evaluate(self, source, **kwargs):
		raise NotImplementedError



class Fitable(Resultable):
	def fit(self, source, **kwargs):
		raise NotImplementedError



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











