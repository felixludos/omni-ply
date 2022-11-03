
from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

from omnibelt import unspecified_argument, duplicate_instance, get_printer


from ..features import Prepared
from ..persistent import Fingerprinted


prt = get_printer(__file__)


class AbstractData(Fingerprinted, Prepared):
	def _prepare(self, source=None, **kwargs):
		pass

	def copy(self):
		return duplicate_instance(self) # shallow copy

	def get(self, key):
		return self.get_from(self, key)

	def get_from(self, source, key):
		return self._get_from(source, key)

	@staticmethod
	def _get_from(source, key):
		raise NotImplementedError


	def _title(self):
		raise NotImplementedError


	def __str__(self):
		return self._title()


	def __repr__(self):
		return str(self)



class AbstractCountableData(AbstractData):
	def __init__(self, default_len=None, **kwargs):
		super().__init__(**kwargs)
		self._default_len = default_len


	def __str__(self):
		return f'{super().__str__()}[{self.size}]'


	class UnknownCount(TypeError):
		def __init__(self):
			super().__init__('did you forget to provide a "default_len" in __init__?')


	def _length(self):
		raise NotImplementedError


	def length(self):
		if self.is_ready:
			return self._length()
		if self._default_len is not None:
			return self._default_len
		raise self.UnknownCount()


	@property
	def size(self):
		return self.length()


	def __len__(self):
		return self.length()


	def _fingerprint_data(self):
		try:
			N = len(self)
		except self.UnknownCount:
			N = None
		return {'len': N, **super()._fingerprint_data()}



class AbstractDataSource(AbstractData):
	def _prepare(self, source=None, **kwargs):
		super()._prepare(source=source, **kwargs)
		for material in self.materials():
			material.prepare()

	def register_material(self, name, material):
		raise NotImplementedError
	
	def _register_material_as(self, material, *names):
		for name in names:
			self.register_material(name, material)
	
	def remove_material(self, name):
		raise NotImplementedError

	def named_materials(self) -> Iterator[Tuple[str, 'AbstractMaterial']]:
		raise NotImplementedError

	def available(self) -> Iterator[str]:
		for k, _ in self.named_materials():
			yield k

	def materials(self) -> Iterator['AbstractMaterial']:
		for _, m in self.named_materials():
			yield m

	class MissingMaterial(KeyError):
		pass

	def get_material(self, name, default=unspecified_argument):
		raise NotImplementedError

	def __contains__(self, name):
		return self.has(name)

	def has(self, key):
		raise NotImplementedError


	def _title(self):
		return self.__class__.__name__

	def __str__(self):
		return f'{super().__str__()}({", ".join(self.available())})'


	View = None
	def view(self, **kwargs):
		return self.View(self, **kwargs)



class AbstractMaterial(AbstractData):
	@staticmethod
	def _get_from(source, key):
		raise NotImplementedError



class AbstractCollection(AbstractMaterial, AbstractDataSource):
	pass
	
	

class AbstractView(AbstractDataSource):
	def __init__(self, source=None, **kwargs):
		super().__init__(**kwargs)

	@property
	def source(self):
		raise NotImplementedError

	def available(self) -> Iterator[str]:
		return self.source.available()

	def has(self, key):
		return self.source.has(key)

	def _title(self):
		return f'{self.__class__.__name__}{"{" + self.source._title() + "}" if self.source is not None else ""}'



class AbstractBatch(AbstractView):
	def __init__(self, progress, **kwargs):
		super().__init__(**kwargs)

	@property
	def size(self):
		raise NotImplementedError

	@property
	def progress(self) -> 'AbstractProgress':
		raise NotImplementedError

	@property
	def source(self):
		return self.progress.source

	def new(self):
		return self.progress.new_batch()
	
	

class AbstractProgression:
	def __iter__(self):
		return self

	def __next__(self):
		return self.next_batch()

	@property
	def current_batch(self):
		raise NotImplementedError

	def next_batch(self):
		raise NotImplementedError

	@property
	def source(self):
		raise NotImplementedError

	def done(self):
		raise NotImplementedError

	@property
	def sample_count(self):
		raise NotImplementedError
	@property
	def batch_count(self):
		raise NotImplementedError



class AbstractBatchable(AbstractDataSource):
	def __iter__(self):
		return self.progression()

	Progression = None
	def progression(self, **kwargs):
		return self.Progression(self, **kwargs)

	def batch(self, batch_size, **kwargs):
		if progress is None:
			progress = self.progression(batch_size=batch_size, **kwargs)
		return progress.current_batch




