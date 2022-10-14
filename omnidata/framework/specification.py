
from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Generator, Type, Iterable, \
	Iterator, NamedTuple, ContextManager
import types
from omnibelt import split_dict, unspecified_argument, agnosticmethod, OrderedSet, \
	extract_function_signature, method_wrapper, agnostic, agnosticproperty, \
	defaultproperty, autoproperty, referenceproperty, smartproperty, cachedproperty, TrackSmart, Tracer
from omnibelt.nodes import AddressNode, SparseNode, AutoAddressNode


class Specification:
	def __iter__(self):
		return iter(self.emit())

	def include(self, *srcs: Union['Specification', 'Specced', Iterable[Tuple[str, 'Hyperparameter']]]):
		raise NotImplementedError

	def emit(self, recursive=True, flat=True, **kwargs) -> Iterator[Tuple[str, 'Hyperparameter']]:
		raise NotImplementedError



class LazySpecification(Specification):
	def __init__(self, *srcs, **kwargs):
		super().__init__(**kwargs)
		self.srcs = []
		self.include(*srcs)

	def include(self, *srcs: Union['Specced.Specification', 'Specced', Iterator[Tuple[str, 'Hyperparameter']]]):
		for src in srcs:
			if isinstance(src, types.GeneratorType):
				src = list(src)
			self.srcs.append(src)

	def _package(self, key, param, trace, delimiter=None, **kwargs):
		if delimiter is not None:
			history = trace.path
			if len(history):
				terms = [k for k, _ in history] + [key]
				key = delimiter.join(terms)
		return key, param

	def _emit_params(self, params, *, trace, recursive=True, **kwargs):
		for key, param in params:
			item = self._package(key, param, trace=trace, **kwargs)
			if item is not None:
				yield item
				if recursive and isinstance(param, Specced): # recursive
					yield from self._emit_src(param, trace=trace.append((key, param)), **kwargs)

	def _emit_src(self, src, **kwargs):
		if isinstance(src, Specification):
			yield from self._emit_params(src.emit(**kwargs), **kwargs)
		elif isinstance(src, Specced):
			yield from self._emit_params(src.full_spec().emit(**kwargs), **kwargs)
		else:
			yield from self._emit_params(src, **kwargs)

	Tracer = Tracer

	def emit(self, recursive=True, flat=True, trace=None, delimiter=None,
	         **kwargs) -> Iterator[Tuple[str, 'Hyperparameter']]:
		if flat and delimiter is None:
			delimiter = '.'
		if trace is None:
			trace = self.Tracer()
		for src in self.srcs:
			yield from self._emit_src(src, trace=trace, recursive=recursive, delimiter=delimiter, **kwargs)



class SpecNode(Specification, AutoAddressNode, SparseNode):
	
	def _include_param(self, key, param, **kwargs):
		raise NotImplementedError

	def _include_src(self, src, **kwargs):
		if isinstance(src, Specification):
			yield from self._emit_params(src.emit(**kwargs), **kwargs)
		elif isinstance(src, Specced):
			yield from self._emit_params(src.full_spec().emit(**kwargs), **kwargs)
		else:
			yield from self._emit_params(src, **kwargs)

	def include(self, *srcs: Union['Specification', 'Specced', Iterable[Tuple[str, 'Hyperparameter']]]):
		for src in srcs:
			if isinstance(src, types.GeneratorType):
				src = list(src)
			self.add(src)
	
	pass



class Specced:
	class Specification(Specification):
		pass

	@agnostic
	def full_spec(self, spec: Optional[Specification] = None) -> Specification:
		if spec is None:
			spec = self.Specification()
		return spec

















