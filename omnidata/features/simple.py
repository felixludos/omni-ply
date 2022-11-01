from omnibelt import unspecified_argument, agnosticproperty


class Named:
	def __init__(self, *args, name=unspecified_argument, **kwargs):
		super().__init__(*args, **kwargs)
		if name is not unspecified_argument:
			self.name = name

	class NoNameError(ValueError):
		pass

	def __str__(self):
		if self.name is None:
			raise self.NoNameError('No name specified')
		return self.name


	@agnosticproperty
	def name(self):
		return getattr(self, '_name', None)
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











