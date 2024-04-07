

from ..core import AbstractGadget, AbstractGame, AbstractGaggle
from ..core.gaggles import GaggleBase
from ..core.gadgets import AbstractGenetic



# class AbstractSpaced(AbstractGadget):
# 	def infer_space(self, ctx: AbstractGame, gizmo: str):
# 		raise NotImplementedError



class AbstractPlan:
	pass



class AbstractStaged:
	@property
	def is_staged(self):
		raise NotImplementedError


	def stage(self, plan: AbstractPlan = None):
		raise NotImplementedError



class Staged(AbstractStaged):
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



class AlreadyStagedError(Exception):
	pass



class Sensitive(AbstractStaged):
	_AlreadyStagedError = AlreadyStagedError

	_is_sensitive = False
	@property
	def is_sensitive(self):
		return self._is_sensitive

	def stage(self, plan: AbstractPlan = None):
		if self.is_sensitive and self.is_staged:
			raise self._AlreadyStagedError(f'{self} is already staged.')
		return super().stage(plan)



class StagedGaggle(GaggleBase, Staged):
	def _stage(self, plan: AbstractPlan):
		for gadget in self._gadgets():
			if isinstance(gadget, Staged):
				gadget.stage(plan)
		return super()._stage(plan)







