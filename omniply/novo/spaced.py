from .imports import *
from .abstract import *



class AbstractSpaced(AbstractTool):
	def space_from(self, ctx: 'AbstractContext', gizmo: str) -> Any:
		raise NotImplementedError


	def space_of(self, gizmo: str) -> Any:
		raise NotImplementedError


	def space_from(self, ctx: 'AbstractContext', gizmo: str) -> Any:
		raise NotImplementedError



class AbstractChangableSpaced(AbstractSpaced):
	def change_space_of(self, gizmo: str, space: Any) -> Any:
		raise NotImplementedError







