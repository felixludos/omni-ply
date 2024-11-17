from .imports import *
from omnibelt.crafts import AbstractCraft
from .abstract import AbstractGear, AbstractGeared, AbstractMechanical
from .errors import MissingMechanicsError
from ..core import AbstractGame
from ..core.gadgets import GadgetFailure
from ..core.genetics import AutoFunctionGadget, FunctionGadget
from ..core.tools import SkillBase, CraftBase#, ToolDecoratorBase, MIMOToolDecorator, AutoToolDecorator



class GearBase(FunctionGadget, AbstractGear):
	def _grab_from(self, ctx: 'AbstractGame') -> Any:
		if self._fn is None:
			raise GadgetFailure
		return super()._grab_from(ctx)



class GearSkill(GearBase, SkillBase):
	pass


class GearCraft(GearBase, CraftBase):
	_GearSkill = GearSkill

	def as_skill(self, owner: 'AbstractCrafty') -> SkillBase:
		"""
		When an AbstractCrafty is instantiated (i.e., `owner`), any crafts accessible by the class (including inherited ones) can be converted to skills.

		Args:
			owner (AbstractCrafty): The owner of the craft.

		Returns:
			ToolSkill: The converted skill.
		"""
		if not isinstance(owner, AbstractGeared):
			print(f'WARNING: {owner} is not an geared, so gears may not work')
		unbound_fn = self._wrapped_content_leaf()
		fn = None if unbound_fn is None else unbound_fn.__get__(owner, type(owner))
		return self._GearSkill(fn=fn, gizmo=self._gizmo, unbound_fn=unbound_fn, base=self)


	@staticmethod
	def _find_context(geared: AbstractGeared) -> AbstractGame:
		mech = None
		if isinstance(geared, AbstractMechanical):
			mech = geared.mechanics()
		# raise MissingMechanicsError(f'Could not find mechanics for {instance}')
		if mech is None:
			return Context(geared.gearbox()) # effectively no caching, and all dependencies must be local
		return mech


	def __get__(self, instance, owner):
		"""
		When accessing ToolCraft instances directly, they behave as regular methods, applying __get__ to the wrapped function.

		Args:
			instance: The instance that the method is being accessed through, or None when the method is accessed through the owner.
			owner: The owner class.

		Returns:
			Callable: The wrapped function.
		"""
		ctx = self._find_context(instance)
		return ctx.grab(self._gizmo)



class AutoGearCraft(GearCraft, AutoFunctionGadget):
	class _GearSkill(GearSkill, AutoFunctionGadget):
		pass



class GearDecorator(AutoGearCraft):
	def __init__(self, gizmo: str, **kwargs):
		super().__init__(gizmo=gizmo, **kwargs)


	def __call__(self, fn):
		assert self._fn is None, f'Cannot reassign function to {self}'
		self._fn = fn
		return self



