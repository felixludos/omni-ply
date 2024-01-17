from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Hashable, Iterator, Iterable, Type, Set
from collections import UserDict
from omnibelt import unspecified_argument, filter_duplicates

from ..structure import spaces
from ..features import Seeded

from .abstract import AbstractContext, AbstractSpaced, AbstractKit, AbstractTool, AbstractAssessible, AbstractScope, \
	AbstractAssessment, AbstractSourcedKit, AbstractMogul, AbstractSchema, AbstractResource, AbstractDynamicContext
from .errors import MissingGizmoError, ToolFailedError
from .assessments import Signatured



class ContextBase(AbstractContext, AbstractSourcedKit, AbstractSpaced, AbstractAssessible, Signatured):
	def context_id(self) -> Hashable:
		return id(self)


	def __str__(self):
		return f'{self.__class__.__name__}({", ".join(self.gizmos())})'


	def vendors(self, gizmo: str) -> Iterator['AbstractTool']:
		for source in self.sources():
			if source.has_gizmo(gizmo):
				yield source


	def _get_from(self, ctx: AbstractContext, gizmo: str):
		for tool in self.vendors(gizmo):
			try:
				return tool.get_from(self, gizmo)
			except ToolFailedError:
				pass
		raise MissingGizmoError(gizmo)


	def space_of(self, gizmo: str) -> spaces.Dim:
		for tool in self.vendors(gizmo):
			try:
				return tool.space_of(gizmo)
			except (AttributeError, ToolFailedError):
				pass


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str):
		return self._get_from(ctx, gizmo)


	def assess(self, assessment: AbstractAssessment):
		super().assess(assessment)
		for source in self.sources():
			if isinstance(source, AbstractAssessible):
				assessment.add_edge(self, source)
				assessment.expand(source)


	def signatures(self, owner = None) -> Iterator['AbstractSignature']:
		for source in self.sources():
			if isinstance(source, Signatured):
				yield from source.signatures(self)



class ScopedContext(ContextBase):
	def __init__(self, *, scope_table=None, **kwargs):
		super().__init__(**kwargs)
		self._scope_table = scope_table or {}


	def clear_scopes(self):
		self._scope_table.clear()


	def scope_for(self, code, default=unspecified_argument):
		try:
			return self._scope_table[code]
		except KeyError:
			if default is unspecified_argument:
				raise
			return default


	def register_scope(self, code, scope):
		self._scope_table[code] = scope



class NestedContext(ContextBase):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._trace = []


	def _add_trace(self, ctx: AbstractContext):
		self._trace.append(ctx)
	def _pop_trace(self, ctx: AbstractContext):
		self._trace.pop()


	def _fallback_get_from(self, gizmo: str):
		for src in reversed(self._trace):
			try:
				return src.get_from(self, gizmo)
			except MissingGizmoError:
				continue
		raise MissingGizmoError(gizmo)


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str):
		if ctx is not self:
			self._add_trace(ctx)

		try:
			val = self._get_from(ctx, gizmo)
		except MissingGizmoError:
			val = self._fallback_get_from(gizmo)

		if ctx is not self:
			self._pop_trace(ctx)

		return val



class ScopeBase(NestedContext, AbstractScope):
	'''
	interface between the internal labels (defined by dev) for a single module,
	and the external labels (defined by the user) for the entire system
	'''
	# def gizmoto(self) -> Iterator[str]: # no mapping
	# 	for gizmo in self._base.gizmos():
	# 		yield self.gizmo_to()
	# 	yield from self.gizmos()


	def _fallback_get_from(self, gizmo: str):
		return super()._fallback_get_from(self.gizmo_from(gizmo))


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str):
		if ctx is not self:
			gizmo = self.gizmo_to(gizmo)
		return super().get_from(ctx, gizmo)



class ApplicationScope(AbstractScope):
	def __init__(self, application: Dict[str,str] = None,  **kwargs):
		if application is None:
			application = {}
		super().__init__(**kwargs)
		self._application = application
		self._reverse_application = {v:k for k,v in application.items()}


	def gizmo_from(self, gizmo: str) -> str:
		return self._reverse_application.get(gizmo, gizmo)


	def gizmo_to(self, external: str) -> str:
		return self._application.get(external, external)



class DynamicContext(ContextBase, AbstractDynamicContext):
	def __init__(self, *, sources=None, **kwargs):
		if sources is None:
			sources = []
		super().__init__(**kwargs)
		prev = []
		if len(sources):
			prev = list(sources)
			sources.clear()
		self._sources = sources
		self.include(*prev)


	def include(self, *sources: AbstractTool): # a source can be a scope
		self._sources.extend(reversed(sources))
		return self


	def sources(self): # N-O
		yield from reversed(self._sources)



class SizedContext(AbstractContext):
	def __init__(self, *args, size=None, **kwargs):
		super().__init__(**kwargs)
		self._size = size


	@property
	def size(self):
		return self._size



class SeededContext(ContextBase, Seeded):
	def _get_from(self, ctx, gizmo):
		with self.default_rng():
			return super()._get_from(ctx, gizmo)



class Cached(SeededContext, UserDict):
	def gizmos(self) -> Iterator[str]:
		yield from filter_duplicates(super().gizmos(), self.cached())


	def is_cached(self, gizmo: str):
		return gizmo in self.data


	def cached(self):
		yield from self.data.keys()


	def clear_cache(self):
		self.data.clear()


	def _get_from(self, ctx, gizmo):
		if self.is_cached(gizmo):
			val = self.data[gizmo]
		else:
			val = super()._get_from(self, gizmo)
			self.data[gizmo] = val # cache loaded val
		if ctx is self:
			return val
		return val[ctx.indices]


	def __str__(self):
		gizmos = [(gizmo if self.is_cached(gizmo) else '{' + gizmo + '}') for gizmo in self.gizmos()]
		return f'{self.__class__.__name__}({", ".join(gizmos)})'



class SimpleScope(ApplicationScope, Cached, DynamicContext):
	def __init__(self, source, **kwargs):
		super().__init__(**kwargs)
		self.include(source)





##########################################################################################

# class Decoder(Function):
# 	@machine('out')
# 	def forward(self, inp):
# 		# do something
# 		return out
#
#
#
# class Autoencoder2:
# 	encoder = submachine(builder='encoder', input='observation', output='latent')
# 	decoder = submachine(builder='decoder', input='latent', output='reconstruction')
#
# 	@machine('loss')
# 	def compute_loss(self, observation, reconstruction):
# 		return self.criterion(reconstruction, observation)


















