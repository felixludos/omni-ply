from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

from omnibelt import unspecified_argument, duplicate_instance, get_printer


from ..features import Prepared
from ..persistent import AbstractFingerprinted
from ..tools.abstract import AbstractTool, AbstractKit, AbstractSourcedKit, \
	AbstractSpaced, AbstractContext, AbstractMogul, AbstractScope, AbstractSchema
from ..tools.errors import MissingGizmoError
from ..tools.moguls import BatchMogul, IteratorMogul, CreativeMogul

from .errors import MissingBuffer


prt = get_printer(__file__)


class AbstractData(AbstractFingerprinted): # TODO: make fingerprinted
	def copy(self):
		return duplicate_instance(self) # shallow copy


	def _title(self):
		return self.__class__.__name__
	@property
	def title(self):
		return self._title()


	def __str__(self):
		return self.title



class AbstractCountableData(AbstractData):
	def _title(self):
		return f'{super()._title()}[{self.size}]'


	@property
	def size(self):
		raise NotImplementedError



class AbstractDataSource(AbstractData, AbstractSpaced, AbstractTool, Prepared):
	# @classmethod
	# def _parse_context(cls, context: AbstractContext):
	# 	return context
	pass


	# def validate_context(self, context: AbstractContext):
	# 	return context


class AbstractDataRouter(AbstractDataSource, AbstractKit):
	_MissingBuffer = MissingBuffer


	def _prepare(self, source=None, **kwargs):
		super()._prepare(source=source, **kwargs)
		for buffer in self.buffers():
			buffer.prepare()


	def named_buffers(self) -> Iterator[Tuple[str, 'AbstractDataSource']]:
		raise NotImplementedError


	def buffers(self) -> Iterator['AbstractDataSource']:
		for name, buffer in self.named_buffers():
			yield buffer


	def tools(self) -> Iterator['AbstractTool']:
		yield from self.buffers()
		yield from super().tools()


	def get_buffer(self, gizmo: str, default: Optional[Any] = unspecified_argument):
		raise NotImplementedError


	def register_buffer(self, gizmo: str, buffer: AbstractTool):
		raise NotImplementedError


	def _register_multi_buffer(self, buffer: AbstractTool, *gizmos: str): # TODO: move downstream (-> mixin)
		for gizmo in gizmos:
			self.register_buffer(gizmo, buffer)


	def remove_buffer(self, name):
		raise NotImplementedError


	def __str__(self):
		return f'{super().__str__()}({", ".join(map(str, self.gizmos()))})'



class AbstractView(AbstractDataSource):
	def __init__(self, source: AbstractDataRouter = None, **kwargs):
		super().__init__(**kwargs)


	def _prepare(self, **kwargs):
		super()._prepare(**kwargs)
		self.source.prepare()


	def _title(self):
		return f'{super()._title()}{"<" + self.source.title + ">" if self.source is not None else ""}'


	@property
	def source(self):
		raise NotImplementedError


	def get_from(self, ctx: AbstractContext, gizmo: str):
		return self.source.get_from(ctx, gizmo)



class AbstractRouterView(AbstractView, AbstractDataRouter):
	def named_buffers(self) -> Iterator[Tuple[str, 'AbstractDataSource']]:
		yield from self.source.named_buffers()


	def buffers(self) -> Iterator['AbstractDataSource']:
		yield from self.source.buffers()


	def gizmos(self) -> Iterator[str]:
		yield from self.source.gizmos()


	def tools(self) -> Iterator['AbstractTool']:
		yield from self.source.tools()


	def vendors(self, gizmo: str) -> Iterator['AbstractTool']:
		yield from self.source.vendors(gizmo)


	def has_gizmo(self, gizmo):
		return self.source.has_gizmo(gizmo)


	def get_buffer(self, gizmo: str, default: Optional[Any] = unspecified_argument):
		return self.source.get_buffer(gizmo, default=default)


	def validate_context(self, selection):
		return self.source.validate_context(selection)




####################



class AbstractViewable(AbstractDataRouter):
	_View = None
	def view(self, **kwargs):
		return self._View(self, **kwargs)



class AbstractViewableRouterView(AbstractRouterView, AbstractViewable):
	def view(self, **kwargs):
		if self._View is None:
			return self.source._View(self, **kwargs)
		return self._View(self, **kwargs)



class AbstractCountableRouterView(AbstractCountableData, AbstractRouterView):
	pass



class AbstractSelector(AbstractScope):
	def compose(self, other: 'AbstractSelector') -> 'AbstractSelector':
		raise NotImplementedError



class AbstractIndexedData(AbstractCountableRouterView):
	def __init__(self, *, indices=None, **kwargs):
		super().__init__(**kwargs)


	@property
	def size(self):
		return len(self.indices)


	@property
	def indices(self):
		raise NotImplementedError



class AbstractProgression(BatchMogul, IteratorMogul, CreativeMogul, AbstractSourcedKit, Prepared):
	def set_source(self, source: AbstractDataSource):
		raise NotImplementedError


	@property
	def current_batch(self) -> 'AbstractBatch':
		raise NotImplementedError


	@property
	def source(self) -> AbstractTool:
		raise NotImplementedError


	def __str__(self):
		return f'{self.__class__.__name__}({self.source})'


	def __next__(self):
		return self.create_batch()


	def create_batch(self, size=None) -> 'AbstractBatch':
		raise NotImplementedError


	def _create_context(self, source=None, **kwargs) -> AbstractContext:
		return super()._create_context(source=self.source, **kwargs)



class AbstractBatch(AbstractCountableRouterView, AbstractSelector):
	def new(self):
		return self.source.create_batch()



class AbstractBatchable(AbstractDataSource, AbstractSchema):
	def __iter__(self):
		return self.iterate()


	def __next__(self):
		return self.batch()


	def iterate(self, batch_size: Optional[int] = unspecified_argument, **kwargs):
		raise NotImplementedError


	def batch(self, batch_size: Optional[int] = unspecified_argument, **kwargs):
		progress = self.iterate(batch_size=batch_size, **kwargs)
		return progress.current_context()



