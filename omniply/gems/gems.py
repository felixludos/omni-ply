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

	def __call__(self, fn: Optional[Union['GemBase', Callable]] = None, **content: str):
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







