

from .abstract import AbstractView



class BasicView(AbstractView):

	def __init__(self, source=None, **kwargs):
		super().__init__(source=source, **kwargs)
		self._source = source

	@property
	def source(self):
		return self._source
	@source.setter
	def source(self, source):
		self._source = source


	pass














