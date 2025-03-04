from .imports import *
from omnibelt.crafts import AbstractCraft
from .abstract import AbstractGear, AbstractGeared, AbstractMechanical, AbstractMechanics
from .errors import MissingMechanicsError, GearFailed, GearGrabError
from ..core import AbstractGame
from ..core.gadgets import GadgetFailed, SingleGadgetBase
from ..core.genetics import AutoFunctionGadget, FunctionGadget
from ..core.tools import AbstractCrafty, AbstractSkill, SkillBase, CraftBase#, ToolDecoratorBase, MIMOToolDecorator, AutoToolDecorator


class GearContext(Context):
	_GrabError = GearGrabError



# class GearSkillBase(SingleGadgetBase, AbstractSkill):
# 	_no_value = object()
# 	def __init__(self, *, base: Optional[AbstractCraft] = None, **kwargs):
# 		super().__init__(**kwargs)
# 		self._base = base
# 		self._cached = self._no_value
#
# 	def _grab_from(self, ctx: AbstractMechanics) -> Any:
# 		raise NotImplementedError
#
#
#
# class GearSkill(FunctionGadget, GearSkillBase, SkillBase, AbstractGear):
# 	def _grab_from(self, ctx: AbstractMechanics) -> Any:
# 		if self._fn is None: # for "ghost" gears
# 			raise GearFailed
# 		return super()._grab_from(ctx)



class GearSkill(FunctionGadget, SkillBase, AbstractGear):
	_no_value = object()

	def __init__(self, *, base: Optional[AbstractCraft] = None, value: Optional[Any] = _no_value, **kwargs):
		super().__init__(**kwargs)
		self._base = base
		self._cached = value


	def update_cache(self, value: Any):
		self._cached = value


	def _grab_from(self, ctx: AbstractMechanics) -> Any:
		if self._cached is not self._no_value:
			return self._cached
		if self._fn is None:  # for "ghost" gears
			raise GearFailed
		return super()._grab_from(ctx)



class GearCraftBase(CraftBase):
	def __init__(self, gizmo: str, **kwargs):
		super().__init__(**kwargs)
		self._gizmo = gizmo


	_GearSkill: Type[GearSkill]
	def as_skill(self, owner: AbstractCrafty, *, gizmo: str = None, **kwargs) -> GearSkill:
		return self._GearSkill(gizmo=gizmo or self._gizmo, base=self, **kwargs)


	@staticmethod
	def _find_context(geared: AbstractGeared) -> AbstractGame:
		mech = None
		if isinstance(geared, AbstractMechanical):
			mech = geared.mechanics()
		if mech is None:
			return GearContext(geared.gearbox()) # effectively no caching, and all dependencies must be local
		return mech


	def __get__(self, instance, owner):
		'''
		The only time a gear craft is called is as a property - in which case it defers to the local mechanics
		'''
		ctx = self._find_context(instance)
		return ctx.grab(self._gizmo)


	def __set__(self, instance: AbstractGeared, value):
		'''
		Setting a gear craft is not allowed
		'''
		box = instance.gearbox()
		for gear in box.vendors(self._gizmo):
			gear.update_cache(value)
			break



class GearCraft(GearCraftBase):
	# note that unlike ToolCraft, GearCraft is not a gadget - it can be used as a gadget
	# through an instantiated object (through its skill)
	_GearSkill = GearSkill


	def __init__(self, gizmo: str, *, fn: Callable = None, **kwargs):
		super().__init__(gizmo=gizmo, **kwargs)
		self._fn = fn


	def as_skill(self, owner: 'AbstractCrafty', fn=None, unbound_fn=None, **kwargs) -> GearSkill:
		"""
		When an AbstractCrafty is instantiated (i.e., `owner`), any crafts accessible by the class (including inherited ones) can be converted to skills.

		Args:
			owner (AbstractCrafty): The owner of the craft.

		Returns:
			ToolSkill: The converted skill.
		"""
		if not isinstance(owner, AbstractGeared):
			print(f'WARNING: {owner} is not an geared, so gears may not work')
		if unbound_fn is None:
			unbound_fn = self._wrapped_content_leaf()
		if fn is None:
			fn = None if unbound_fn is None else unbound_fn.__get__(owner, type(owner))
		return super().as_skill(owner, fn=fn, unbound_fn=unbound_fn, **kwargs)



class AutoGearCraft(GearCraft):
	class _GearSkill(GearSkill, AutoFunctionGadget):
		pass



class GearDecorator(AutoGearCraft):
	def __call__(self, fn):
		assert self._fn is None, f'Cannot reassign function to {self}'
		self._fn = fn
		return self



# region Static Gears



# class StaticGearSkill(GearSkillBase, AbstractGear):
# 	def __init__(self, gizmo: str, value: Any, **kwargs):
# 		super().__init__(gizmo=gizmo, **kwargs)
# 		self._value = value
#
# 	def _grab_from(self, ctx: 'AbstractGame') -> Any:
# 		return self._value
#
#
#
# class StaticGearCraft(GearCraftBase):
# 	def __init__(self, gizmo: str, value: Any, **kwargs):
# 		super().__init__(gizmo=gizmo, **kwargs)
# 		self._value = value
#
#
# 	_no_value = object()
# 	_GearSkill = StaticGearSkill
# 	def as_skill(self, owner: 'AbstractCrafty', value: Any = _no_value, **kwargs) -> StaticGearSkill:
# 		return super().as_skill(owner, value=self._value if value is self._no_value else value, **kwargs)

# endregion
