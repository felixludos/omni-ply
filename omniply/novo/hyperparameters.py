from .imports import *



class Hyperparameter:
	_unknown = object()

	def __init__(self, default=unspecified_argument, *, fget=None, fset=None, fdel=None, fformat=None, cache=True,
	             attrname=None, **kwargs):
		if default is unspecified_argument:
			default = self._unknown
		super().__init__(**kwargs)
		self.attrname = attrname
		# if not cache:
		# 	raise NotImplementedError('cache=False not implemented') # TODO: implement
		self.cache = cache
		self.default = default
		self.fget = fget
		self.fformat = fformat
		self.fset = fset
		self.fdel = fdel


		pass







