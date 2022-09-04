from collections import OrderedDict
from omnibelt import unspecified_argument, agnosticmethod
from omnibelt.nodes import SubNode


class Specification:
	def find(self, key):
		raise NotImplementedError
	def has(self, key):
		raise NotImplementedError


class PowerSpec(Specification, SubNode):
	def __init__(self, payload=unspecified_argument, *, parent=unspecified_argument, **kwargs):
		super().__init__(**kwargs)
		self._payload = payload
		self._parent = parent


	@property
	def payload(self):
		return OrderedDict([(key, value.payload) for key, value in self._sub.items()]) \
			if self._payload is unspecified_argument else self._payload
	@payload.setter
	def payload(self, value):
		self._payload = value


	@property
	def parent(self):
		return None if self._parent is unspecified_argument else self._parent


	pass






class TreeSpec(Specification, SubNode):
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





