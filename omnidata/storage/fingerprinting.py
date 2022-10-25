from typing import Union, Any, Callable, Type, Iterable, Iterator, Optional, List, Dict, Tuple, Sequence, Hashable, \
	NamedTuple, ContextManager
import numpy as np
import torch
from omnibelt import unspecified_argument, agnosticmethod, md5, primitive, JSONABLE

# TODO: make exportable
# .fp -> hash
# .fpd -> data


class AbstractFingerprinted:
	@property
	def fingerprint(self):
		raise NotImplementedError



class AbstractFingerprint(AbstractFingerprinted):
	@property
	def fingerprint(self):
		return self

	class ExtractionError(ValueError):
		def __init__(self, obj):
			super().__init__(obj)
			self.obj = obj

	# @staticmethod
	# def _obj_type(obj):
	# 	if isinstance(obj, type):
	# 		return f'!type:{obj.__module__}.{obj.__name__}'
	# 	obj = type(obj)
	# 	return f'{obj.__module__}.{obj.__name__}'

	@classmethod
	def extract_data(cls, obj) -> JSONABLE:
		if isinstance(obj, primitive):
			return obj
		# if isinstance(obj, (np.ndarray, torch.Tensor)):
		# 	numels = np.product(obj.shape).item()
		# 	sel = torch.randint(numels, size=(min(5, numels),),
		# 	        generator=torch.Generator().manual_seed(16283393149723337453)).tolist()
		# 	return [obj.sum().item(), obj.reshape(-1)[sel].tolist()]
		if isinstance(obj, (list, tuple)):
			return [cls.extract_data(o) for o in obj]
		if isinstance(obj, dict):
			return [[cls.extract_data(k), cls.extract_data(v)] for k, v in sorted(obj.items())]
		raise cls.ExtractionError(obj)

	def __eq__(self, other):
		return isinstance(other, AbstractFingerprint) and self.check_fingerprint(other)

	def __hash__(self):
		return hash(self.code())

	def code(self):
		return md5(self.data())

	def data(self):
		raise NotImplementedError

	class UnknownObjectError(TypeError):
		pass

	def check_fingerprint(self, obj: Union['AbstractFingerprint', AbstractFingerprinted]):
		if isinstance(obj, AbstractFingerprinted):
			return self == obj.fingerprint
		if not isinstance(obj, AbstractFingerprint):
			raise self.UnknownObjectError(obj)
		return self.code() == obj.code()



class Fingerprinted(AbstractFingerprinted):
	class Fingerprint(AbstractFingerprint):
		def __init__(self, src=None, *, data=None, code=None, **kwargs):
			super().__init__(src=src, **kwargs)
			self.src = src
			self._data = data
			self._code = code

		@classmethod
		def extract_data(cls, obj) -> JSONABLE:
			if isinstance(obj, Fingerprinted):
				return obj._fingerprint_data()
			return super().extract_data(obj)


		class NoObjectError(AttributeError):
			pass

		@property
		def src(self):
			src = getattr(self, '_src', None)
			if src is None:
				raise self.NoObjectError(src)
			return src
		@src.setter
		def src(self, src):
			self._src = src

		def data(self):
			if self._data is None:
				self._data = self.extract_data(self.src)
			return self._data

		def code(self):
			if self._code is None:
				self._code = super().code()
			return self._code

	@property
	def fingerprint(self):
		return self.Fingerprint(self)

	def _fingerprint_data(self):
		return {'cls': self.__class__.__name__, 'module': self.__module__}






