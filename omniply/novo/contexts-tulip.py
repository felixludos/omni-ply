from .kits import *



class Gig(AbstractGig):
	def _grab_from_fallback(self, error: GadgetFailedError, ctx: Optional['AbstractGig'], gizmo: str) -> Any:
		if ctx is None or ctx is self:
			raise AssemblyFailedError(gizmo, error)
			# raise error from error
		return ctx.grab(gizmo)


	def _grab(self, gizmo: str) -> Any:
		return super().grab_from(self, gizmo)


	def grab_from(self, ctx: Optional['AbstractGig'], gizmo: str) -> Any:
		try:
			out = self._grab(gizmo)
		except GadgetFailedError as error:
			out = self._grab_from_fallback(error, ctx, gizmo)
		return self.package(out, gizmo=gizmo)



class Cached(AbstractGig, UserDict):
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


	# def _find_from(self, ctx: AbstractContext, gizmo: str) -> Any:
	# 	val = super().grab_from(ctx, gizmo)
	# 	self.data[gizmo] = val  # cache loaded val
	# 	return val


	def grab_from(self, ctx: Optional['AbstractGig'], gizmo: str) -> Any:
		if self.is_cached(gizmo):
			return self.data[gizmo]
		val = super().grab_from(ctx, gizmo)
		self.data[gizmo] = val  # cache loaded val
		return val



########################################################################################################################


class SimpleGroup(Gig, AbstractGroup):
	_current_context: Optional[AbstractGig]

	def __init__(self, *, apply: Optional[Dict[str, str]] = None, **kwargs):
		if apply is None:
			apply = {}
		super().__init__(**kwargs)
		self._raw_apply = apply
		self._raw_reverse_apply = None
		self._current_context = None


	@property
	def internal2external(self) -> Dict[str, str]:
		return self._raw_apply
	@internal2external.setter
	def internal2external(self, value: Dict[str, str]):
		self._raw_apply = value
		self._raw_reverse_apply = None


	@property
	def external2internal(self) -> Dict[str, str]:
		# return self._infer_external2internal(self._raw_apply, self.gizmoto())
		if self._raw_reverse_apply is None:
			self._raw_reverse_apply = self._infer_external2internal(self._raw_apply, self._gizmos())
		return self._raw_reverse_apply


	@staticmethod
	# @lru_cache(maxsize=None)
	def _infer_external2internal(raw: Dict[str, str], products: Iterator[str]) -> Dict[str, str]:
		reverse = {}

		for product in products:
			if product in raw:
				external = raw[product]
				if external in reverse:
					raise ApplicationAmbiguityError(product, [reverse[external], product])
				reverse[external] = product

		return reverse


	def gizmo_from(self, gizmo: str) -> str:
		return self.external2internal.get(gizmo, gizmo)


	def gizmo_to(self, gizmo: str) -> str:
		return self.internal2external.get(gizmo, gizmo)


	def _grab_from_fallback(self, error: GadgetFailedError, ctx: Optional['AbstractGig'], gizmo: str) -> Any:
		return super()._grab_from_fallback(error, self._current_context, self.gizmo_to(gizmo))


	def grab_from(self, ctx: Optional['AbstractGig'], gizmo: str) -> Any:
		if ctx is not None and ctx is not self:
			assert self._current_context is None, f'Context already set to {self._current_context}'
			self._current_context = ctx
			gizmo = self.gizmo_from(gizmo) # convert to internal gizmo
		return super().grab_from(self, gizmo)


