
from .quirks import *
from .kits import *
from .contexts import *


class AbstractBehavior(AbstractQuirk):
	# def realize(self, instance: T, owner: Type[T]) -> Any:
	# 	'''creates the quirk ab initio for the instance (usually when no default value is provided)'''
	# 	raise NotImplementedError

	pass



class BuiltBehavior(DefaultQuirk, AbstractBehavior):
	def __init__(self, default: Optional[Any] = unspecified_argument, *,
	             builder: Optional['AbstractBuilder'] = None, **kwargs):
		super().__init__(default, **kwargs)
		self._builder = builder


	def reach(self, owner: Optional[Type[T]] = None) -> Any:
		raise NotImplementedError


	def realize(self, instance: T, owner: Optional[Type[T]] = None) -> Any:
		if self._default is self._missing_value:
			if self._builder is None:
				raise self._MissingValueError(self)
			return self._builder.build(instance, owner=owner)
		return self._default



class TraitKit(AbstractTool): # TODO: should this be an AbstractMultiTool?
	'''
	delegates work to submodule by accessing it with `getattr(self.owner, self.attrname)`
	(thereby building lazily)
	'''

	def __init__(self, owner: AbstractCrafty, base: AbstractBehavior, attrname: str, **kwargs):
		super().__init__(**kwargs)
		self._attrname = attrname
		self._owner = owner
		self._base = base


	def gizmos(self):
		return getattr(self._owner, self._attrname).gizmos()


	def get_from(self, ctx: Optional['AbstractContext'], gizmo: str,
	             default: Optional[Any] = unspecified_argument) -> Any:
		return getattr(self._owner, self._attrname).get_from(ctx, gizmo, default=default)



class ScopeTraitKit(Context, TraitKit):
	pass



class AbstractTrait(AbstractBehavior, AbstractToolKit, AbstractCraft):
	# submachine -> trait

	# def emit_craft_items(self, owner: Union[Type[AbstractCrafty], AbstractCrafty] = None):
	# 	'''
	# 	technically, Crafts allow owners to be types, but when processing the crafts, an AbstractCrafty instance
	# 	is always used as owner.
	#
	# 	TODO: handle the case where the owner is a type (for static analysis)
	# 	'''
	#
	# 	if isinstance(owner, type):
	# 		raise NotImplementedError(f'{owner!r} must be an instance (static analysis not implemented yet)')

	_Skill = TraitKit
	def as_skill(self, owner: AbstractCrafty):
		return self._Skill(owner=owner, base=self, attrname=self._attrname)














