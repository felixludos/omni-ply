from typing import Optional, Any, Iterator, Hashable, Type
from omnibelt import unspecified_argument, filter_duplicates

from ..structure import spaces

from .errors import ToolFailedError, MissingGizmoError



class Gizmoed:
	def gizmos(self) -> Iterator[str]:
		raise NotImplementedError


	def has_gizmo(self, gizmo: str) -> bool:
		raise NotImplementedError


	def vendors(self, gizmo: str) -> Iterator['AbstractTool']:
		yield from self.tools()


	def tools(self) -> Iterator['AbstractTool']:
		raise NotImplementedError



class SingleVendor(Gizmoed):
	def vendor(self, gizmo: str, default: Any = unspecified_argument) -> 'AbstractTool':
		raise NotImplementedError


	def vendors(self, gizmo: str) -> Iterator['AbstractTool']:
		yield self.vendor(gizmo)



class AbstractTool(Gizmoed): # leaf/source

	_ToolFailedError = ToolFailedError
	_MissingGizmoError = MissingGizmoError

	def tools(self) -> Iterator['AbstractTool']:
		yield self


	# def validate_context(self, ctx: 'AbstractContext'):
	# 	'''makes sure the context is valid for this tool, and returns a new context if necessary'''
	# 	return ctx


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str):
		raise NotImplementedError


	def get(self, gizmo: str, default: Any = unspecified_argument):
		try:
			return self.get_from(None, gizmo)
		except ToolFailedError:
			if default is unspecified_argument:
				raise
			return default


	def __getitem__(self, gizmo: str):
		return self.get_from(None, gizmo)


	def __contains__(self, gizmo: str):
		return self.has_gizmo(gizmo)



class AbstractKit(AbstractTool): # branch/router
	def tools(self) -> Iterator['AbstractTool']: # must iterate over children, not self (prevents infinite recursion)
		raise NotImplementedError


	def gizmos(self) -> Iterator[str]:
		yield from filter_duplicates(*[tool.gizmos() for tool in self.tools()])


	def has_gizmo(self, gizmo: str) -> bool:
		return any(tool.has_gizmo(gizmo) for tool in self.vendors(gizmo))


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str):
		tries = 0
		for tool in self.vendors(gizmo):
			try:
				return tool.get_from(ctx, gizmo)
			except ToolFailedError:
				tries += 1
		raise self._ToolFailedError(f'No tool for {gizmo} in {self} (tried {tries} tool/s)')



class AbstractSourcedKit(AbstractKit):
	def sources(self) -> Iterator['AbstractTool']:
		raise NotImplementedError


	def gizmos(self) -> Iterator[str]:
		yield from filter_duplicates(*[source.gizmos() for source in self.sources()])


	def tools(self) -> Iterator['AbstractTool']:
		for source in self.sources():
			yield from source.tools()



class AbstractContext(AbstractKit):
	@property
	def context_id(self) -> Hashable:
		raise NotImplementedError


	def __hash__(self):
		return hash(self.context_id)


	def __eq__(self, other):
		if isinstance(other, AbstractContext):
			return self.context_id == other.context_id
		return NotImplemented


	def get(self, gizmo: str, default: Any = unspecified_argument):
		try:
			return self.get_from(self, gizmo)
		except ToolFailedError:
			if default is unspecified_argument:
				raise
			return default


	def __getitem__(self, gizmo: str):
		return self.get_from(self, gizmo)



class AbstractDynamicKit(AbstractKit):
	def include(self, *sources: AbstractTool) -> 'AbstractDynamicKit':
		raise NotImplementedError



class AbstractDynamicContext(AbstractContext, AbstractDynamicKit):
	def include(self, *sources: AbstractTool) -> 'AbstractDynamicContext':
		raise NotImplementedError



class AbstractResourceable(AbstractTool):
	def as_resource(self, mogul: 'AbstractMogul') -> 'AbstractResource':
		raise NotImplementedError



class AbstractResource:
	def validate_context(self, ctx: AbstractContext) -> AbstractContext:
		return ctx



class AbstractScopable(AbstractResource, AbstractTool):
	'''
	 A tool can specify a scope for the given context to use when accessing its gizmos.

	 For example, datasets can specify a scope for the context to use when accessing their data.

	 Can raise a `InvalidContextError` if the context is not valid for this tool
	 (e.g. if it doesn't have the required data, like a `size`)
	 '''
	def create_scope(self, ctx: AbstractContext) -> Optional['AbstractTool']:
		return self


	def validate_context(self, ctx: AbstractContext) -> AbstractContext:
		scope = self.as_scope(ctx)
		return ctx if scope is None else ctx.include(scope)



class AbstractScopeGenerator(AbstractResource, AbstractTool):
	'''
	 A tool can specify a scope for the given context to use when accessing its gizmos.

	 For example, datasets can specify a scope for the context to use when accessing their data.

	 Can raise a `InvalidContextError` if the context is not valid for this tool
	 (e.g. if it doesn't have the required data, like a `size`)
	 '''
	def as_scope(self, ctx: AbstractContext) -> Optional['AbstractScope']:
		pass


	def validate_context(self, ctx: AbstractContext) -> AbstractContext:
		scope = self.as_scope(ctx)
		return ctx if scope is None else scope



class AbstractMogul: # controls/manages/creates/generates contexts => trainers, experiments, etc.
	def resources(self) -> Iterator[AbstractResource]:
		raise NotImplementedError



class AbstractScope(AbstractContext):
	def gizmoto(self) -> Iterator[str]: # iterates over external gizmos (products)
		yield from self.gizmos()


	def gizmo_to(self, external: str) -> str: # global -> local
		return external


	def gizmo_from(self, internal: str) -> str: # local -> global
		return internal



class AbstractReproducableScope(AbstractScopable, AbstractScope):
	pass



##########################################################################################



class AbstractSpaced:
	def space_of(self, gizmo: str) -> spaces.Dim:
		raise ToolFailedError(gizmo)



class AbstractChangableSpace(AbstractSpaced): # TODO: build into `space` crafts
	def change_space_of(self, gizmo: str, space: spaces.Dim):
		raise NotImplementedError


	def _missing_spaces(self):
		# yield from (gizmo for gizmo in self.gizmos() if self.space_is_missing(gizmo))
		raise NotImplementedError


	def clear_space(self, gizmo: str) -> bool:
		raise NotImplementedError



class AbstractSchema(AbstractSpaced): # context for building
	pass


##########################################################################################



class AbstractAssessment:
	def add_node(self, node, **props):
		raise NotImplementedError


	def add_edge(self, src, dest, **props):
		raise NotImplementedError


	def expand(self, node: 'AbstractAssessible'):
		node.assess(self)


	def expand_static(self, node: Type['AbstractAssessible']):
		node.assess_static(self)



class AbstractAssessible:
	@classmethod
	def assess_static(cls, assessment: AbstractAssessment):
		assessment.add_node(cls)


	def assess(self, assessment: AbstractAssessment):
		assessment.add_node(self)



class Loggable:
	@staticmethod
	def log(ctx):
		raise NotImplementedError






