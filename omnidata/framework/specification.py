from collections import OrderedDict
from omnibelt import unspecified_argument, agnosticmethod
from omnibelt.nodes import TreeNode


class Specification:
	def find(self, key):
		raise NotImplementedError
	def has(self, key):
		raise NotImplementedError



class TreeSpec(Specification, TreeNode):
	def find(self, key):
		return self.sub(key)


	def has(self, key):
		return key in self._sub


	@classmethod
	def from_python(cls, data, *, parent=unspecified_argument):
		node = cls(parent=parent)
		if isinstance(data, dict):
			return DictSpec({key: TreeSpec.from_python(value, parent=parent) for key, value in data.items()}, parent=parent)
		elif isinstance(data, list):
			return ListSpec([TreeSpec.from_python(value, parent=parent) for value in data], parent=parent)
		else:
			return TreeSpec(data, parent=parent)



class TreeSpecification:

	pass





