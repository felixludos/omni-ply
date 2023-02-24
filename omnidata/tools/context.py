from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
from collections import UserDict

from .abstract import AbstractContext, AbstractTool, AbstractScope
from .errors import MissingGizmoError, ToolFailedError


class ContextBase(AbstractContext):
	def _get_from(self, ctx: Optional['AbstractContext'], gizmo: str):
		for tool in self.vendors(gizmo):
			try:
				return tool.get_from(self, gizmo)
			except ToolFailedError:
				pass
		raise MissingGizmoError(gizmo)


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str):
		return self._get_from(ctx, gizmo)



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
			val = self._get_from(self, gizmo)
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
	def __init__(self, base: AbstractTool, **kwargs):
		super().__init__(**kwargs)
		self._base = base


	def gizmoto(self) -> Iterator[str]: # no mapping
		yield from self._base.gizmos()


	def _fallback_get_from(self, gizmo: str):
		return super()._fallback_get_from(self.gizmo_from(gizmo))


	def _get_from(self, ctx: Optional['AbstractContext'], gizmo: str):
		return self._base.get_from(self, gizmo)


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str):
		if ctx is not self:
			gizmo = self.gizmo_to(gizmo)
		return super().get_from(ctx, gizmo)


# class MapScope()



class SimpleContext(ContextBase):
	def __init__(self, tools=None, **kwargs):
		if tools is None:
			tools = []
		super().__init__(**kwargs)
		self._tools = tools


	def add_tool(self, tool):
		self._tools.append(tool)
	def add_tools(self, tools):
		for tool in tools:
			self.add_tool(tool)


	def tools(self):
		yield from self._tools



class ScopedContext(SimpleContext):
	_Scope = ScopeBase

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._vendors = {}
		self._scopes = []


	def _as_scope(self, tool):
		if isinstance(tool, AbstractScope):
			return tool
		return self._Scope(tool)


	def add_scope(self, scope):
		self._scopes.append(scope)
		for gizmo in scope.gizmoto():
			self._vendors[gizmo] = scope


	def add_tool(self, tool):
		self.add_scope(self._as_scope(tool))
		super().add_tool(tool)


	def vendors(self, gizmo: str) -> Iterator['AbstractScope']:
		yield self._vendors[gizmo]


	def scopes(self):
		yield from self._vendors.values()



class SizedContext(ContextBase):
	@property
	def size(self):
		return self._size

	def __init__(self, *args, size=None, **kwargs):
		super().__init__(**kwargs)
		self._size = size



class Cached(ContextBase, UserDict):
	def _get_from(self, ctx, gizmo):
		if gizmo in self:
			return self[gizmo]
		val = super()._get_from(ctx, gizmo)
		self[gizmo] = val # cache loaded val
		return val



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


















