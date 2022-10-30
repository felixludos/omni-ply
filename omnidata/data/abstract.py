

from omnibelt import unspecified_argument, duplicate_instance

from ..features import Prepared
from ..persistent import Fingerprinted



class AbstractData(Fingerprinted, Prepared):

	def _fingerprint_data(self):
		return {'ready': self.is_ready, **super()._fingerprint_data()}


	def get(self, source=None, *keys):
		if source is None:
			source = self
		return self._get(source, *keys)
	
	
	def _get(source, *keys):
		raise NotImplementedError


	pass


class AbstractDataSource(AbstractData):

	def available(self):
		raise NotImplementedError
	
	
	def loaded(self):
		raise NotImplementedError
	

	def has(self, key):
		raise NotImplementedError

	
	pass



class AbstractMaterial:
	def load(self, source=None):
		raise NotImplementedError
	


