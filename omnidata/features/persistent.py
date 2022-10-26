import os
from pathlib import Path
from omnibelt import unspecified_argument, agnostic, agnosticproperty


class Rooted:
	_DEFAULT_MASTER_ROOT = os.getenv('OMNIDATA_PATH', 'local_data/')

	_root = None
	def __init__(self, root=unspecified_argument, **kwargs):
		super().__init__(**kwargs)
		if root is not unspecified_argument:
			self._root = root


	@classmethod
	def _infer_root(cls, root=None):
		if root is None:
			root = cls._DEFAULT_MASTER_ROOT
		root = Path(root)
		os.makedirs(str(root), exist_ok=True)
		return root


	@agnostic
	def get_root(self): # for easier inheritance
		return self._infer_root(self._root)


	@agnosticproperty
	def root(self):
		return self.get_root()













