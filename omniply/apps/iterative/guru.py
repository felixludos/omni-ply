from .imports import *

from .abstract import AbstractMogul, AbstractGuru



class GuruBase(AbstractGuru):
	_Gift: Type[AbstractGig] = Context


	def _guide_sparks(self):
		raise NotImplementedError


	def guide(self, base: AbstractMogul | Iterable[AbstractGadget] = None) -> Iterator[AbstractGig]:
		for spark in self._guide_sparks():
			ctx = self._Gift(spark) if spark is not None else self._Gift()
			if isinstance(self, AbstractGadget):
				ctx.include(self)
			if base is not None:
				ctx.extend(base.gadgetry() if isinstance(base, AbstractMogul) else base)
			yield ctx


	def __iter__(self):
		return self.guide()


	def __next__(self):
		return next(self.guide())



