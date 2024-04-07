from .imports import *

from .abstract import AbstractGuru, AbstractInnovator



class InnovatorBase(AbstractInnovator):
	_Innovation: Type[AbstractGame] = Context


	def _generate_sparks(self):
		raise NotImplementedError


	def innovate(self, base: AbstractGuru | Iterator[AbstractGadget] = None) -> Iterator[AbstractGame]:
		for spark in self._generate_sparks():
			ctx = self._Innovation(spark) if spark is not None else self._Innovation()
			if isinstance(self, AbstractGadget):
				ctx.include(self)
			if base is not None:
				ctx.extend(base.resources() if isinstance(base, AbstractGuru) else base)
			yield ctx


	def __iter__(self):
		return self.innovate()


	def __next__(self):
		return next(self.innovate())



