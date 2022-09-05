from collections import OrderedDict
from omnibelt import unspecified_argument, agnosticmethod
from omnibelt.nodes import TreeNode, AutoTreeNode


class Specification:
	def find(self, key):
		raise NotImplementedError
	def has(self, key):
		raise NotImplementedError



class TreeSpec(AutoTreeNode, Specification):
	def find(self, key):
		return self.get(key)



class Specced:

	@classmethod
	def build_from_spec(cls, spec, **kwargs):
		pass





