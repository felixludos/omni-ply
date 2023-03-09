from typing import Tuple, Iterator, Dict

from .abstract import AbstractAssessible, AbstractAssessment


class AbstractSignature:
	pass


class SimpleSignature(AbstractSignature):
	def __init__(self, output, inputs=(), meta=(), **props):
		if isinstance(inputs, str):
			inputs = (inputs,)
		# inputs = tuple(inputs)
		if isinstance(meta, str):
			meta = (meta,)
		# meta = tuple(meta)
		super().__init__()
		self.inputs = inputs
		self.meta = meta
		self.output = output
		self.props = props


	def replace(self, fixes: Dict[str,str]):
		raise NotImplementedError


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
		return f'{self.output} <- {ant}'



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


















