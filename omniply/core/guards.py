from typing import Callable, Any
from .tools import ToolDecoratorBase, ToolCraft



class ToolGuard:
	def __init__(self, cond: Callable[[...], bool] = None, **kwargs):
		super().__init__(**kwargs)
		self._cond = cond
		self._effect = None

	def __call__(self, fn: Callable[[...], Any]) -> 'ToolGuard':
		if self._cond is None:
			self._cond = fn
			return self
		return self.effect(fn)

	def effect(self, effect: Callable[[...], Any]) -> 'ToolGuard':
		if self._effect is not None:
			raise ValueError('ToolGuard already has effect')
		self._effect = effect
		return self



class GuardedToolDecorator(ToolDecoratorBase):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._guards = []

	_ToolGuard = ToolGuard
	def guard(self, cond: Callable[[...], bool] = None, **kwargs) -> ToolGuard:
		guard = self._ToolGuard(cond, **kwargs)
		self._guards.append(guard)
		return guard




















