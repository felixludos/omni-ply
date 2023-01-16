from tqdm import tqdm

from omnibelt import unspecified_argument, agnosticproperty


class Named:
	_name = None


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
			self._is_ready = True
			self._prepare(*args, **kwargs)
		return self


	def _prepare(self, *args, **kwargs):
		pass


class ProgressBarred:
	_pbar_owner = None
	_pbar_cls = tqdm
	_pbar_instance = None

	@classmethod
	def replace_pbar_cls(cls, pbar):
		cls._pbar_owner._pbar_cls = pbar

	@classmethod
	def _create_pbar(cls, *args, **kwargs):
		if cls._pbar is not None:
			cls._close_pbar()
		cls._pbar_owner._pbar = cls._pbar_cls(*args, **kwargs)
		return cls._pbar

	@agnosticproperty
	def _pbar(self):
		return self._pbar_owner._pbar_instance

	@classmethod
	def _close_pbar(cls):
		if cls._pbar is not None:
			cls._pbar.close()
			cls._pbar = None

ProgressBarred._pbar_owner = ProgressBarred





