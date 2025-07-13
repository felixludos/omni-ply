from .imports import *
from .abstract import AbstractGem, AbstractGeologist
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
	
	def build(self, fn: Callable[[Any], Any]) -> Self:
		self._build_fn = fn
		return self

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

	def resolve(self, instance: AbstractGeologist):
		val = instance.__dict__.get(self._name, self._no_value)
		if val is self._realizing_flag:
			fn = self._fn
			self._fn = None
			del instance.__dict__[self._name]# = self._no_value
			try:
				val = super().resolve(instance)
			except self._NoValueError as e:
				raise self._ResolutionLoopError(f'Gem {self._name} is in a resolution loop with {e}')
			else:
				self._fn = fn
		elif val is self._no_value and self._fn is not None:
			instance.__dict__[self._name] = self._realizing_flag
			val = self.realize(instance)
			if self._cache:
				if self._name is None:
					raise NoNameError(f'Gem {self.__class__.__name__} has no name')
				instance.__dict__[self._name] = val
		else:
			val = super().resolve(instance)
		return val
	


class FinalizedGem(CachableGem):
	def __init__(self, default: Optional[Any] = GemBase._no_value, *, final: bool = False, **kwargs):
		super().__init__(default=default, **kwargs)
		self._final = final

	def revise(self, instance, value):
		if self._final:
			raise RevisionsNotAllowedError(self._name)
		return super().revise(instance, value)



class InheritableGem(GemBase):
	def __init__(self, default: Optional[Any] = GemBase._no_value, *, inherit: bool = True, **kwargs):
		super().__init__(default=default, **kwargs)
		self._inherit = inherit

	@property
	def inherit(self):
		return self._inherit


class GeodeBase(GemBase):
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

	def __init__(self, *args, exclusive: bool = None, insulated: bool = None, **kwargs):
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
		cfg = instance._my_config

		# if default is self._no_value:
		# 	if self._fn is None:
		# 		default = self._default
		# 	else:
		# 		default = self._fn.__get__(instance, instance.__class__)()
		#
		# elif default is self._no_value:
		# 	if default is self._no_value:
		# 		if self._fn is None:
		# 			return cfg.pulls(*self._aliases, self._name, silent=self._silent)
		# 		else:
		# 			default = self._fn.__get__(instance, instance.__class__)()
		if default is self._no_value:
			return cfg.pulls(*self._aliases, self._name, silent=self._silent)
		return cfg.pulls(*self._aliases, self._name, default=default, silent=self._silent)

	def revitalize(self, instance: fig.Configurable):
		"""
		Called after construction to enable eager resolution.
		"""
		if self._eager and isinstance(instance, fig.Configurable):

			self.revise()
			

			raise NotImplementedError
		




