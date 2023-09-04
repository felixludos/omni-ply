
from .quirks import *
from .kits import *
from .contexts import *


class AbstractQuality(AbstractQuirk):
	# def realize(self, instance: T, owner: Type[T]) -> Any:
	# 	'''creates the quirk ab initio for the instance (usually when no default value is provided)'''
	# 	raise NotImplementedError

	_ReachFailedFlag = ReachFailedFlag
	def reach(self, owner: Optional[Type[T]] = None) -> Any:
		'''tries accessing the quirk without creating it (eg. for static analysis)'''
		raise self._ReachFailedFlag



class AbstractTrait(AbstractQuality, AbstractCraft):
	pass



class TemplateQuality(DefaultQuirk, AbstractQuality):
	def __init__(self, default: Optional[Any] = unspecified_argument, *,
	             tmpl: Optional[Type] = None, **kwargs):
		super().__init__(default, **kwargs)
		self._template = tmpl


	def _replicator_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
		if 'tmpl' not in kwargs:
			kwargs['tmpl'] = self._template
		return kwargs


	def reach(self, owner: Optional[Union[T, Type[T]]] = None) -> Any:
		return self._template


	def realize(self, instance: T, owner: Optional[Type[T]] = None) -> Any:
		if self._default is self._missing_value:
			return self.reach(instance)()
		return self._default



class ArtQuality(DefaultQuirk, AbstractQuality):
	'''caches the artist in the instance's __dict__ using _builder_key() as key'''
	def __init__(self, default: Optional[Any] = unspecified_argument, *,
	             artist: Optional['AbstractArtist'] = None, **kwargs):
		super().__init__(default, **kwargs)
		self._artist = artist


	def _replicator_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
		if 'artist' not in kwargs:
			kwargs['artist'] = self._artist
		return kwargs


	def reach(self, owner: Optional[Union[T, Type[T]]] = None) -> Any:
		'''creates a new artist'''
		return self._create_builder(owner) # TODO: maybe consolidate


	def realize(self, instance: T, owner: Optional[Type[T]] = None) -> Any:
		if self._default is self._missing_value:
			return self.reach(instance).design_for(instance)
		return self._default


	def _create_builder(self, owner: Optional[Union[T, Type[T]]] = None) -> 'AbstractArtist':
		if self._artist is None:
			raise self._MissingValueError(self)

		raise NotImplementedError  # TODO: implement this



class CachedArtQuality(ArtQuality):
	def _builder_key(self, owner: Optional[Union[T, Type[T]]] = None):
		return f'__builder_for_{self._attrname}'


	def realize(self, instance: T, owner: Optional[Type[T]] = None) -> Any:
		product = super().realize(instance, owner=owner)
		# remove cached artist after realizing the trait
		key = self._builder_key(owner)
		if hasattr(owner, key):
			delattr(owner, key)
		return product


	def reach(self, owner: Optional[Union[T, Type[T]]] = None) -> Any:
		if owner is None: # caching not possible (eg. static analysis)
			return super().reach(owner)

		key = self._builder_key(owner)
		artist = getattr(owner, key, None) # TODO: consider accessing __dict__ directly
		if artist is not None:
			return artist

		artist = self._create_builder(owner)
		setattr(owner, key, artist)
		return artist



class TraitTool(AbstractGadget): # TODO: should this be an AbstractMultiTool?
	'''
	delegates work to submodule by accessing it with `getattr(self.owner, self.attrname)`
	(thereby building lazily)
	'''
	def __init__(self, owner: AbstractCrafty, attrname: str, **kwargs):
		super().__init__(**kwargs)
		self._owner = owner
		self._attrname = attrname


	def _resolve_tool(self):
		return getattr(self._owner, self._attrname)


	def gizmos(self):
		return self._resolve_tool().gizmos()


	def grab_from(self, ctx: Optional['AbstractGig'], gizmo: str) -> Any:
		tool = self._resolve_tool()
		return tool.grab_from(ctx, gizmo)


	def __repr__(self):
		return f'[{self._attrname}]({", ".join(self.gizmos())})'



class ScopeTraitKit(TraitTool):
	def grab_from(self, ctx: 'AbstractScopedContext', gizmo: str) -> Any:
		return self._resolve_tool().grab_from(ctx.scope_for(self), gizmo)



class SimpleTrait(DescriptorQuirk, AbstractTrait):
	_Skill = TraitTool
	def as_skill(self, owner: AbstractCrafty, **kwargs):
		return self._Skill(owner=owner, attrname=self._attrname, **kwargs)



class AppliedTraitTool(SimpleGroup, TraitTool, AbstractMultiTool): # TODO: should this be an AbstractMultiTool?
	'''
	delegates work to submodule by accessing it with `getattr(self.owner, self.attrname)`
	(thereby building lazily)
	'''



class AppliedTrait(SimpleTrait):
	# submachine -> appliedtrait
	def __init__(self, *, apply: Optional[Dict[str, str]] = None, **kwargs):
		# apply is the mapping the dev specifies to map the trait's gizmos to the owner's gizmos
		super().__init__(**kwargs)
		self._apply = apply


	_Skill = AppliedTraitTool
	def as_skill(self, owner: AbstractCrafty, apply=unspecified_argument, **kwargs):
		if apply is unspecified_argument:
			apply = self._apply
		return super().as_skill(owner=owner, apply=apply, **kwargs)










