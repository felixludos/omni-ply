from .imports import *
from .abstract import *
from .kits import *



class Context(AbstractContext):
	def get(self, gizmo: str, default: Any = unspecified_argument):
		try:
			return self.get_from(None, gizmo)
		except ToolFailedError:
			if default is unspecified_argument:
				raise
			return default


	def __getitem__(self, item):
		return self.get(item)


	def _get_from_fallback(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		return ctx.get_from(self, gizmo)


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
		try:
			return super().get_from(self, gizmo)
		except ToolFailedError:
			if ctx is None or ctx is self:
				raise
			return self._get_from_fallback(ctx, gizmo)



class Cached(AbstractContext, UserDict):
	def __repr__(self):
		gizmos = [(gizmo if self.is_cached(gizmo) else '{' + gizmo + '}') for gizmo in self.gizmos()]
		return f'{self.__class__.__name__}({", ".join(gizmos)})'


	def gizmos(self) -> Iterator[str]:
		yield from filter_duplicates(self.cached(), super().gizmos())


	def is_cached(self, gizmo: str) -> bool:
		return gizmo in self.data


	def cached(self) -> Iterator[str]:
		yield from self.data.keys()


	def clear_cache(self) -> None:
		self.data.clear()


	def _find_from(self, ctx: AbstractContext, gizmo: str) -> Any:
		val = super().get_from(ctx, gizmo)
		self.data[gizmo] = val  # cache loaded val
		return val


	def get_from(self, ctx: Optional[AbstractContext], gizmo: str) -> Any:
		val = self.data[gizmo] if self.is_cached(gizmo) else self._find_from(ctx, gizmo)
		return val



########################################################################################################################



class AbstractGang(AbstractContext):
	pass
	# def gizmoto(self) -> Iterator[str]: # iterates over internal gizmos (products)
	# 	for external in self.gizmos():
	# 		yield self.gizmo_to(external)
	#
	#
	# def gizmo_from(self, gizmo: str) -> str:
	# 	return gizmo
	#
	#
	# def gizmo_to(self, external: str) -> str: # global -> local
	# 	return external
	#
	#
	# def _get_from_fallback(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
	# 	return ctx.get_from(self, gizmo)
	#
	#
	# def get_from(self, ctx: Optional['AbstractContext'], gizmo: str) -> Any:
	# 	if ctx is self:
	# 		return super().get_from(self, gizmo)
	# 	try:
	# 		return super().get_from(self, gizmo)
	# 	except ToolFailedError:
	# 		if ctx is None or ctx is self:
	# 			raise
	# 		return self._get_from_fallback(ctx, gizmo)



class SimpleGang(AbstractGang):
	_raw_reverse_apply = None

	def __init__(self, *, apply: Optional[Dict[str, str]] = None, **kwargs):
		if apply is None:
			apply = {}
		super().__init__(**kwargs)
		self._raw_apply = apply
		self._context_path = []


	def gizmoto(self) -> Iterator[str]:
		yield from super().gizmos()


	def gizmos(self) -> Iterator[str]:
		for gizmo in self.gizmoto():
			yield self.gizmo_to(gizmo)


	@property
	def internal2external(self) -> Dict[str, str]:
		return self._raw_apply
	@internal2external.setter
	def internal2external(self, value: Dict[str, str]):
		self._raw_apply = value
		self._raw_reverse_apply = None


	@property
	def external2internal(self) -> Dict[str, str]:
		if self._raw_reverse_apply is None:
			self._raw_reverse_apply = self._infer_external2internal(self._raw_apply, self.gizmoto())
		return self._raw_reverse_apply


	@staticmethod
	# @lru_cache(maxsize=None)
	def _infer_external2internal(raw: Dict[str, str], products: Iterator[str]) -> Dict[str, str]:
		reverse = {}

		for internal, external in raw.items():
			reverse.setdefault(external, []).append(internal)

		external2internal = {}
		for product in products:
			if product in external2internal:
				options = reverse[product]
				if len(options) > 1:
					raise ApplicationAmbiguityError(product, options)
				external2internal[product] = options[0]

		return external2internal


	def gizmo_from(self, gizmo: str) -> str:
		return self.external2internal.get(gizmo, gizmo)


	def gizmo_to(self, external: str) -> str:
		return self.internal2external.get(external, external)


	def _fallback_get_from(self, gizmo: str):
		return super()._fallback_get_from(self.gizmo_to(gizmo))


	def get_from(self, ctx: Optional[AbstractContext], gizmo: str):
		if ctx is not self: # coming from external context
			self._context_path.append(gizmo)
			gizmo = self.gizmo_to(gizmo)
			out = super().get_from(self, gizmo)

		return super().get_from(ctx, gizmo)


