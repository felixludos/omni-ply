
from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

from omnibelt import unspecified_argument, duplicate_instance, get_printer


from ..features import Prepared
from ..persistent import Fingerprinted


prt = get_printer(__file__)


class AbstractData(Fingerprinted, Prepared):

	# def _fingerprint_data(self):
	# 	return {'ready': self.is_ready, **super()._fingerprint_data()}


	def get(self, *keys):
		return self._get_from(self, *keys)


	def get_from(self, source=None, *keys):
		if source is None:
			source = self
		return self._get_from(source, *keys)

	def _prepare(self, source=None, **kwargs):
		pass

	@staticmethod
	def _get_from(source, *keys):
		raise NotImplementedError



class AbstractDataSource(AbstractData):

	def available(self) -> Iterator[str]:
		raise NotImplementedError
	

	def has(self, key):
		raise NotImplementedError


	def _title(self):
		return self.__class__.__name__

	def __str__(self):
		return f'{self._title()}({", ".join(self.available())})'


	View = None
	def view(self, **kwargs):
		return self.View(self, **kwargs)

	pass


class ExpectingDataSource(AbstractDataSource):
	def __init_subclass__(cls, materials=None, required_materials=None, **kwargs):
		super().__init_subclass__(**kwargs)
		if required_materials is not None:
			raise NotImplementedError
		if isinstance(materials, str):
			materials = [materials]
		base = getattr(cls, '_expecting_materials', [])
		cls._expecting_materials = base + (materials or [])


	def _prepare(self, source=None, **kwargs):
		super()._prepare(source=source, **kwargs)
		for material in self._expecting_materials:
			if not self.has(material):
				prt.warning(f'Expected material {material!r} not found in {self}')



class CachedDataSource(AbstractDataSource):
	def cached(self) -> Iterator[str]:
		raise NotImplementedError

	def __str__(self):
		cached = set(self.cached())
		return f'{self._title()}(' \
		       f'{", ".join((key if key in cached else "{" + key + "}") for key in self.available())})'



class AbstractMaterial(AbstractData):
	@staticmethod
	def _get_from(source, *keys):
		raise NotImplementedError



class AbstractCollection(AbstractMaterial):
	def materials(self):
		raise NotImplementedError


	def named_materials(self):
		raise NotImplementedError
	
	

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

	pass









