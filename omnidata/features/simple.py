from omnibelt import unspecified_argument


class Named:
	def __init__(self, *args, name=unspecified_argument, **kwargs):
		super().__init__(*args, **kwargs)
		if name is not unspecified_argument:
			self.name = name


	def __str__(self):
		return self.name


	@property
	def name(self):
		try:
			return self._name
		except AttributeError:
			return getattr(self.__class__, 'name', self.__class__.__name__)
	@name.setter
	def name(self, name):
		self._name = name




class Prepared: # TODO: add autoprepare using __certify__
	@property
	def is_ready(self):
		return getattr(self, '_is_ready', False)


	class NotReady(Exception):
		pass


	def prepare(self, *args, **kwargs):
		if not self.is_ready:
			self._prepare(*args, **kwargs)
			self._is_ready = True
		return self


	def _prepare(self, *args, **kwargs):
		pass











