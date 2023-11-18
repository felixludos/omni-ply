from .errors import *



class ToolBase(AbstractGadget):
	_ToolFailedError = GadgetFailedError
	_MissingGizmoError = MissingGizmoError


	# def _grab_from(self, ctx: AbstractContext, gizmo: str) -> Any:
	# 	raise NotImplementedError


	# def grab_from(self, ctx: Optional[AbstractContext], gizmo: str,
	#               default: Optional[Any] = unspecified_argument) -> Any:
	# 	try:
	# 		return self._grab_from(ctx, gizmo)
	# 	except self._ToolFailedError:
	# 		if default is unspecified_argument:
	# 			raise
	# 		return default


class SingleGizmoTool(ToolBase):
	def __init__(self, gizmo: str, **kwargs):
		super().__init__(**kwargs)
		self._gizmo = gizmo

	def gizmos(self) -> Iterator[str]:
		yield self._gizmo

	def gives(self, gizmo: str) -> bool:
		return gizmo == self._gizmo


class FunctionTool(SingleGizmoTool):
	def __init__(self, gizmo: str, fn: Callable, **kwargs):
		super().__init__(gizmo=gizmo, **kwargs)
		self._fn = fn


	def __repr__(self):
		name = getattr(self._fn, '__qualname__', None)
		if name is None:
			name = getattr(self._fn, '__name__', None)
		return f'{self.__class__.__name__}({name}: {self._gizmo})'


	@property
	def __call__(self):
		return self._fn#.__get__(None, type(None))


	def __get__(self, instance, owner):
		return self._fn.__get__(instance, owner)
		if instance is None:
			return self
		return self._fn.__get__(instance, owner)


	@staticmethod
	def _extract_gizmo_args(fn: Callable, ctx: AbstractGig,
							args: Optional[Tuple] = None, kwargs: Optional[Dict[str, Any]] = None) \
			-> Tuple[Tuple, Dict[str, Any]]:
		return extract_function_signature(fn, default_fn=lambda gizmo, default: ctx.grab_from(ctx, gizmo))


	def grab_from(self, ctx: Optional['AbstractGig'], gizmo: str) -> Any:
		if gizmo != self._gizmo:
			raise self._MissingGizmoError(gizmo)
		return self._fn(ctx)



class AutoFunctionTool(FunctionTool):
	@staticmethod
	def _extract_gizmo_args(fn: Callable, ctx: AbstractGig,
							args: Optional[Tuple] = None, kwargs: Optional[Dict[str, Any]] = None) \
			-> Tuple[Tuple, Dict[str, Any]]:
		return extract_function_signature(fn, default_fn=lambda gizmo, default: ctx.grab_from(ctx, gizmo))


	def grab_from(self, ctx: Optional['AbstractGig'], gizmo: str) -> Any:
		if gizmo != self._gizmo:
			raise self._MissingGizmoError(gizmo)

		args, kwargs = self._extract_gizmo_args(self._fn, ctx)
		return self._fn(*args, **kwargs)



class ToolSkill(AbstractSkill):
	def __init__(self, *, unbound_fn: Callable, base: Optional[AbstractCraft] = None, **kwargs):
		super().__init__(**kwargs)
		self._unbound_fn = unbound_fn
		self._base = base
		

	@property
	def __call__(self):
		return self._unbound_fn
	

	def __get__(self, instance, owner):
		if instance is None:
			return self
		return self._unbound_fn.__get__(instance, owner)




class FunctionSkill(FunctionTool, ToolSkill):
	pass


class AutoFunctionSkill(AutoFunctionTool, ToolSkill):
	pass


class ToolCraft(FunctionTool, NestableCraft):
	def _wrapped_content(self): # wrapped method
		return self._fn


	_ToolSkill = FunctionSkill
	def as_skill(self, owner: AbstractCrafty) -> ToolSkill:
		unbound_fn = self._wrapped_content_leaf()
		fn_name = getattr(unbound_fn, '__name__', None)
		if fn_name is None:
			fn = unbound_fn.__get__(owner, type(owner))
		else:
			fn = getattr(owner, fn_name) # get most recent version of method
		return self._ToolSkill(self._gizmo, fn=fn, unbound_fn=unbound_fn, base=self)



class AutoFunctionToolCraft(AutoFunctionTool, NestableCraft):
	def _wrapped_content(self): # wrapped method
		return self._fn


	_ToolSkill = AutoFunctionSkill
	def as_skill(self, owner: AbstractCrafty):
		unbound_fn = self._wrapped_content_leaf()
		fn_name = getattr(unbound_fn, '__name__', None)
		if fn_name is None:
			fn = unbound_fn.__get__(owner, type(owner))
		else:
			fn = getattr(owner, fn_name) # get most recent version of method
		return self._ToolSkill(self._gizmo, fn=fn, unbound_fn=unbound_fn, base=self)



class ToolDecorator(ToolBase):
	def __init__(self, gizmo: str, **kwargs):
		super().__init__(**kwargs)
		self._gizmo = gizmo


	def gizmos(self) -> Iterator[str]:
		yield self._gizmo


	def gives(self, gizmo: str) -> bool:
		return gizmo == self._gizmo


	def grab_from(self, ctx: Optional['AbstractGig'], gizmo: str) -> Any:
		raise self._ToolFailedError(gizmo)


	_ToolCraft = ToolCraft
	def _actualize_tool(self, fn: Callable, **kwargs):
		return self._ToolCraft(self._gizmo, fn=fn, **kwargs)


	def __call__(self, fn):
		return self._actualize_tool(fn)



class AutoToolDecorator(ToolDecorator):
	_ToolCraft = AutoFunctionToolCraft


