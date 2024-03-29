

from ..core import AbstractGadget, AbstractGig, AbstractGaggle
from ..core.gaggles import GaggleBase
from ..core.gadgets import AbstractGenetic



class AbstractSpaced(AbstractGadget):
	def infer_space(self, ctx: AbstractGig, gizmo: str):
		raise NotImplementedError



class AbstractPlan(AbstractSpaced):
	pass



class Staged:
	_is_staged = False
	@property
	def is_staged(self):
		return self._is_staged


	def stage(self, plan: AbstractPlan = None):
		if not self.is_staged:
			self._stage(plan)
			self._is_staged = True
		return self


	def _stage(self, plan: AbstractPlan):
		pass



class StagedGaggle(GaggleBase):
	def _stage(self, plan: AbstractPlan):
		for gadget in self._vendors():
			if isinstance(gadget, Staged):
				gadget.stage(plan)







