from .. import spaces
from ..models import ModelBuilder
from .estimators import JointEstimator, ScikitEstimatorWrapper, Regressor, Classifier, Periodized



class AbstractScikitBuilder(ModelBuilder):

	pbar = None
	num_workers = None

	JointEstimator = JointEstimator
	def create_joint(self, din, dout, estimators, **kwargs):
		return self.JointEstimator(estimators, din=din, dout=dout, pbar=self.pbar, num_workers=self.num_workers,
		                           **kwargs)


	def create_regressor(self, din, dout):
		if isinstance(dout, spaces.Periodic):
			return self.create_periodic(din, dout)
		return self.create_sequential(din, dout)


	Periodized = Periodized
	def create_periodic(self, din, dout, component_dim=None):
		if component_dim is None:
			component_dim = spaces.Bound(-1, 1)
		return self.Periodized([self.create_regressor(din=din, dout=component_dim),
		                        self.create_regressor(din=din, dout=component_dim)])


	def create_sequential(self, din, dout):
		raise NotImplementedError


	def create_classifier(self, din, dout):
		raise NotImplementedError


	class InvalidDimError(Exception):
		def __init__(self, din, dout):
			super().__init__(f'din={din}, dout={dout}')
			self.din, self.dout = din, dout


	def build(self, din=None, dout=None):
		if din is None:
			din = getattr(self, 'din', None)
		if dout is None:
			dout = getattr(self, 'dout', None)
		if din is None or dout is None:
			source = getattr(self, 'source', None)
			if source is None:
				raise self.MissingKwargsError('din', 'dout', 'source')
			if din is None:
				din = source.din
			if dout is None:
				dout = source.dout

		if isinstance(dout, spaces.Joint):
			return self.create_joint(din, dout, [self.build(din=din, dout=dim) for dim in dout])

		elif isinstance(dout, spaces.Categorical):
			return self.create_classifier(din, dout)

		elif isinstance(dout, spaces.Continuous):
			return self.create_regressor(din, dout)

		raise self.InvalidDimError(din=din, dout=dout)



class AbstractScikitWrapperBuilder(AbstractScikitBuilder):


	class SequentialWrapper(Regressor, ScikitEstimatorWrapper):
		pass


	def create_sequential(self, din, dout):
		return self.SequentialWrapper(self.create_scikit_regressor(din=din, dout=dout), din=din, dout=dout)


	class ClassifierWrapper(Classifier, ScikitEstimatorWrapper):
		pass


	def create_classifier(self, din, dout):
		return self.ClassifierWrapper(self.create_scikit_classifier(din=din, dout=dout), din=din, dout=dout)


	def create_scikit_regressor(self, din, dout):
		raise NotImplementedError


	def create_scikit_classifier(self, din, dout):
		raise NotImplementedError








