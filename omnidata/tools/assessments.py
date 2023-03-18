from typing import Tuple, Iterator, Dict

from .abstract import AbstractAssessible, AbstractAssessment, AbstractTool


class AbstractSignature:
	pass


class SimpleSignature(AbstractSignature):
	def __init__(self, output, inputs=(), meta=(), *, name=None, fn=None, **props):
		if isinstance(inputs, str):
			inputs = (inputs,)
		# inputs = tuple(inputs)
		if isinstance(meta, str):
			meta = (meta,)
		# meta = tuple(meta)
		if name is None and fn is not None:
			name = fn.__name__
		super().__init__()
		self.inputs = inputs
		self.meta = meta
		self.output = output
		self.props = props
		self.name = name
		self.fn = fn


	def __contains__(self, label: str):
		return label in self.inputs or label in self.meta or label == self.output


	def copy(self, output=None, inputs=None, meta=None, props=None, **kwargs):
		if output is None:
			output = self.output
		if inputs is None:
			inputs = self.inputs
		if meta is None:
			meta = self.meta
		if props is None:
			props = self.props
		return type(self)(output, inputs, meta, **{**props, **kwargs})


	def replace(self, fixes: Dict[str,str], **kwargs):
		new = self.copy(output=fixes.get(self.output, self.output), inputs=tuple(fixes.get(i, i) for i in self.inputs),
		                meta=tuple(fixes.get(m, m) for m in self.meta), **kwargs)
		return new


	def __str__(self):
		inp = ', '.join(self.inputs)
		ant = '()'
		if self.inputs and self.meta:
			raise NotImplementedError
			ant = f'{inp} ({", ".join(self.meta)})'
		elif self.meta:
			ant = ', '.join(f'<{m}>' for m in self.meta)
		elif self.inputs:
			ant = inp
		# msg = f'{self.output} <- {ant}'
		msg = f'{ant} -> {self.output}'
		if self.name:
			msg = f'{self.name}: {msg}'
		return msg


	def __repr__(self):
		return f'{self.__class__.__name__}({self.inputs} -> {self.output})'



class Signatured:
	_Signature = SimpleSignature

	def signatures(self, owner = None) -> Iterator['AbstractSignature']:
		raise NotImplementedError



class SimpleAssessment(AbstractAssessment):
	class Node:
		def __init__(self, node, **props):
			self.node = node
			self.props = props

		def __eq__(self, other):
			return id(self.node) == id(other.node)

		def __hash__(self):
			return id(self.node)


	class Edge:
		def __init__(self, src, dest, **props):
			self.src = src
			self.dest = dest
			self.props = props

		def __eq__(self, other):
			return (id(self.src), id(self.dest)) == (id(other.src), id(other.dest))

		def __hash__(self):
			return hash((id(self.src), id(self.dest)))


	def __init__(self):
		self.nodes = set()
		self.edges = set()


	def add_edge(self, src, dest, **props):
		self.edges.add(self.Edge(src, dest, **props))
		self.add_node(src)
		self.add_node(dest)


	def add_node(self, node, **props):
		self.nodes.add(self.Node(node, **props))


















