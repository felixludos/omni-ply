from .imports import *
from .abstract import AbstractGem, AbstractGeologist, AbstractGeode
from .errors import NoValueError, ResolutionLoopError, NoNameError, RevisionsNotAllowedError
from omnibelt import unspecified_argument, AbstractStaged
from omnibelt.crafts import InheritableCrafty, AbstractCraft, NestableCraft



class GemBase(NestableCraft, AbstractGem):
	_no_value = object()
	def __init__(self, default: Optional[Any] = _no_value, *, final: bool = None, **kwargs):
		"""note that this does allow """
		super().__init__(**kwargs)
		self._name = None
		self._owner = None
		self._default = default
		if isinstance(default, Callable):
			self._fn = default
			self._default = self._no_value
		self._final = final
		# self._content = [] # TODO: a new subclass of GemBase can enable multiple fns
		self._fn = None
		self._build_fn = None

	def __call__(self, fn: Optional[Union['GemBase', Callable]] = None):
		self._fn = fn
		return self

	_NoValueError = NoValueError
	def realize(self, instance: AbstractGeologist):
		if self._fn is None:
			if self._default is self._no_value:
				raise self._NoValueError(self._name)
			val = self._default
		else:
			val = self._fn.__get__(instance, instance.__class__)()
		return self.rebuild(instance, val)

	def resolve(self, instance: AbstractGeologist):
		val = instance.__dict__.get(self._name, self._no_value)
		if val is self._no_value:
			val = self.realize(instance)
			if self._cache:
				if self._name is None:
					raise NoNameError(f'Gem {self.__class__.__name__} has no name')
				instance.__dict__[self._name] = val
		return val
	
	def build(self, fn: Callable[[Any], Any]) -> 'Self':
		self._build_fn = fn
		return fn

	def rebuild(self, instance: AbstractGeologist, value: Any):
		if self._build_fn is None:
			return value
		build_fn = self._build_fn.__get__(instance, instance.__class__)
		built = build_fn(value)
		return built
	
	def revise(self, instance: AbstractGeologist, value: Any):
		raise RevisionsNotAllowedError(self._name)

	def _wrapped_content(self): # wrapped method
		return self._fn

	def __repr__(self):
		return f'{self.__class__.__name__}({self._name})'

	def __set_name__(self, owner, name):
		self._name = name
		self._owner = owner


class CachableGem(GemBase):
	def __init__(self, default: Optional[Any] = GemBase._no_value, *, cache: bool = True, **kwargs):
		super().__init__(default=default, **kwargs)
		self._cache = cache

	def resolve(self, instance: AbstractGeologist):
		val = instance.__dict__.get(self._name, self._no_value)
		if val is self._no_value:
			val = self.realize(instance)
			if self._cache:
				if self._name is None:
					raise NoNameError(f'Gem {self.__class__.__name__} has no name')
				instance.__dict__[self._name] = val
		return val

	def revise(self, instance, value):
		if self._name is None:
			raise NoNameError(f'Gem {self.__class__.__name__} has no name')
		value = self.rebuild(instance, value)
		instance.__dict__[self._name] = value


class LoopyGem(CachableGem):
	_realizing_flag = object()
	_ResolutionLoopError = ResolutionLoopError

	def realize(self, instance: AbstractGeologist):
		try:
			return super().realize(instance)
		except self._ResolutionLoopError:
			if self._fn is not None and self._default is not self._no_value:
				fn = self._fn
				self._fn = None
				val = super().realize(instance)
				self._fn = fn
				return val
			raise

	def resolve(self, instance: AbstractGeologist):
		val = instance.__dict__.get(self._name, self._no_value)
		if val is self._realizing_flag:
			raise self._ResolutionLoopError(f'{self._name}')
		elif val is self._no_value:
			instance.__dict__[self._name] = self._realizing_flag
			val = self.realize(instance)
			if self._cache:
				if self._name is None:
					raise NoNameError(f'Gem {self.__class__.__name__} has no name')
				instance.__dict__[self._name] = val
		return val
	


class FinalizedGem(CachableGem):
	def __init__(self, default: Optional[Any] = GemBase._no_value, *, final: bool = False, **kwargs):
		super().__init__(default=default, **kwargs)
		self._final = final

	def revise(self, instance, value):
		if self._final:
			raise RevisionsNotAllowedError(self._name)
		return super().revise(instance, value)


class LockableGem(CachableGem):
	def __init__(self, default: Optional[Any] = GemBase._no_value, *, lock: bool = False, **kwargs):
		super().__init__(default=default, **kwargs)
		self._lock = lock

	def lock(self, set_to: bool = True):
		self._lock = set_to

	def unlock(self):
		self._lock = False

	def revise(self, instance: AbstractStaged, value):
		if self._lock and isinstance(instance, AbstractStaged) and instance.is_staged:
			raise RevisionsNotAllowedError(self._name)
		return super().revise(instance, value)


class InheritableGem(GemBase):
	def __init__(self, default: Optional[Any] = GemBase._no_value, *, inherit: bool = True, **kwargs):
		super().__init__(default=default, **kwargs)
		self._inherit = inherit

	@property
	def inherit(self):
		return self._inherit


class GeodeBase(GemBase, AbstractGeode):
	def restage(self, instance: AbstractGeologist, scape: Mapping[str, Any] = None):
		value = self.resolve(instance)
		if isinstance(value, AbstractStaged):
			return value.stage(scape)

	def relink(self, instance: AbstractGeologist) -> Iterator[AbstractGadget]:
		value = self.resolve(instance)
		if isinstance(value, AbstractGadget):
			yield value


from ..core import Gate, Mechanism

class MechanismGeode(GeodeBase):
	_Gate = Gate
	_Mechanism = Mechanism

	def __init__(self, *args, exclusive: bool = True, insulated: bool = None, **kwargs):
		super().__init__(*args, **kwargs)
		self._exclusive = exclusive
		self._insulated = insulated
		self._first_group = None
		self._second_group = None

	def __call__(self, *args, **kwargs):
		if len(args) and isinstance(args[0], Callable):
			assert not len(args) > 1, f'{self.__class__.__name__} can only take one function'
			assert not len(kwargs), f'{self.__class__.__name__} can only take one function'
			self._fn = args[0]
		elif self._first_group is None:
			self._first_group = args if len(args) else None, kwargs
		elif self._second_group is None:
			if len(args) or self._first_group[0] is not None:
				raise TypeError(f'{self.__class__.__name__} require a single group, '
									f'for example `{self.__class__.__name__}(...)(*args, **kwargs)`')
			self._second_group = kwargs
		else:
			raise TypeError(f'{self.__class__.__name__} can only take two groups of arguments')
		return self

	def _build_gadget(self, gadget: AbstractGadget) -> AbstractGadget:
		if self._first_group is not None:
			if self._second_group is None:
				select, gate = self._first_group
				return self._Gate(gadget, select=select, gate=gate,
								  exclusive=self._exclusive, insulated=self._insulated)
			external, internal = self._first_group[1], self._second_group
			return self._Mechanism(gadget, external=external, internal=internal,
									exclusive=self._exclusive, insulated=self._insulated)

	def relink(self, instance: AbstractGeologist) -> Iterator[AbstractGadget]:
		for gadget in super().relink(instance):
			yield self._build_gadget(gadget)

	def revise(self, instance: AbstractGeologist, value: Any):
		super().revise(instance, value)
		instance.refresh_geodes(self._name)


import omnifig as fig

class ConfigGem(GemBase):
	"""
	A gem that can be configured with a function to build its value.
	"""
	def __init__(self, *args, alias: Iterable[str] = None, eager: bool = True, silent: bool = None, **kwargs):
		if alias is None:
			alias = []
		if isinstance(alias, str):
			alias = [alias]
		super().__init__(*args, **kwargs)
		self._eager = eager
		self._silent = silent
		self._aliases = tuple(alias)

	def _from_config(self, instance: fig.Configurable, default: Any = GemBase._no_value) -> Any:
		cfg = getattr(instance, '_my_config', None)
		if cfg is not None:
			if default is self._no_value:
				return cfg.pulls(*self._aliases, self._name, silent=self._silent)
			return cfg.pulls(*self._aliases, self._name, default=default, silent=self._silent)
		return default

	def revitalize(self, instance: fig.Configurable):
		if self._eager and isinstance(instance, fig.Configurable):
			self.resolve(instance)

	def realize(self, instance: AbstractGeologist):
		default = self._default
		if self._fn is not None:
			default = self._fn.__get__(instance, instance.__class__)()

		val = self._from_config(instance, default)
		if val is self._no_value:
			raise self._NoValueError(self._name)
		return self.rebuild(instance, val)


from ..gears.gears import AutoGearCraft, GearSkill, AbstractGeared, SkipGear


class GearGem(AutoGearCraft, CachableGem):
	# TODO: add feature to eagerly grab + cache all geargems in stage()
	class _GearSkill(AutoGearCraft._GearSkill):
		def __init__(self, *, owner: 'AbstractCrafty' = None, cache: bool = True, **kwargs):
			super().__init__(**kwargs)
			self._owner = owner
			self._auto_cache = cache
			self._cached = False

		def update_cache(self, value: Any):
			self._cached = True
			self._base.revise(self._owner, value)

		def _grab_from(self, ctx: 'AbstractMechanics') -> Any:
			if self._fn is None or (self._cached and self._auto_cache):  # for "ghost" gears
				try:
					return self._base.resolve(self._owner)
				except self._NoValueError:
					if self._fn is None:
						raise SkipGear
			value = super(GearSkill, self)._grab_from(ctx)
			self.update_cache(value)
			return value


	def __init__(self, gizmo: str, *, default: Optional[Any] = GemBase._no_value, auto_cache: bool = True, 
			  fn: Callable = None, **kwargs):
		super().__init__(gizmo=gizmo, default=default, fn=None, **kwargs)
		self._auto_cache = auto_cache
		self._gear_fn = fn

	def _wrapped_content(self):
		return self._gear_fn
	
	def __call__(self, fn: Callable):
		self._gear_fn = fn
		return self

	def as_skill(self, owner: 'AbstractCrafty', 
			  fn: Callable = None, unbound_fn: Callable = None, **kwargs) -> GearSkill:
		if not isinstance(owner, AbstractGeared):
			print(f'WARNING: {owner} is not an geared, so gears may not work')
		if unbound_fn is None:
			unbound_fn = self._wrapped_content_leaf()
		if fn is None:
			fn = None if unbound_fn is None else unbound_fn.__get__(owner, type(owner))
		return self._GearSkill(gizmo=self._gizmo, base=self, owner=owner, fn=fn, unbound_fn=unbound_fn,
						 cache=self._auto_cache, **kwargs)



