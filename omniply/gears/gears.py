from .imports import *
from .abstract import AbstractGear, AbstractGeared, AbstractMechanical
from .errors import MissingMechanicsError
from ..core import AbstractGame
from ..core.gadgets import FunctionGadget
from ..core.tools import SkillBase, CraftBase, ToolDecoratorBase, MIMOToolDecorator, AutoToolDecorator, AutoMIMOFunctionGadget



class GearSkill(SkillBase, AbstractGear):
	pass



class GearCraft(FunctionGadget, AbstractGear, CraftBase):
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
		fn = unbound_fn.__get__(owner, type(owner))
		return self._GearSkill(fn=fn, gizmo=self._gizmo, unbound_fn=unbound_fn, base=self)


	@staticmethod
	def _find_context(geared: AbstractGeared) -> AbstractGame:
		mech = None
		if isinstance(geared, AbstractMechanical):
			mech = geared.mechanics()
		# raise MissingMechanicsError(f'Could not find mechanics for {instance}')
		if mech is None:
			return Context(geared.gearbox()) # effectively no caching
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



class AutoGearCraft(AutoMIMOFunctionGadget, GearCraft):
	class _GearSkill(AutoMIMOFunctionGadget, GearSkill):
		pass



class GearDecorator(MIMOToolDecorator):
	_ToolCraft = GearCraft



class AutoGearDecorator(AutoToolDecorator):
	_ToolCraft = AutoGearCraft


