import os
from pathlib import Path
from omnibelt import unspecified_argument, agnostic, agnosticproperty


class Rooted:
	_DEFAULT_MASTER_ROOT = os.getenv('OMNIDATA_PATH', 'local_data/')

	@agnostic
	def _infer_root(self, root=None):
		if root is None:
			root = self._DEFAULT_MASTER_ROOT
		root = Path(root)
		# os.makedirs(str(root), exist_ok=True)
		return root


	@agnosticproperty
	def root(self):
		return self._infer_root()













