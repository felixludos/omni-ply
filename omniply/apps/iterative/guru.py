from .imports import *

from .abstract import AbstractGuru, AbstractGod



class GodBase(AbstractGod):
	_Gift: Type[AbstractGame] = Context


	def _guide_sparks(self):
		raise NotImplementedError


	def grant(self, base: AbstractGuru | Iterable[AbstractGadget] = None) -> Iterator[AbstractGame]:
		for spark in self._guide_sparks():
			ctx = self._Gift(spark) if spark is not None else self._Gift()
			if isinstance(self, AbstractGadget):
				ctx.include(self)
			if base is not None:
				ctx.extend(base.gadgetry() if isinstance(base, AbstractGuru) else base)
			yield ctx


	def __iter__(self):
		return self.grant()


	def __next__(self):
		return next(self.grant())



