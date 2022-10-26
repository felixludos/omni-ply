

from omnibelt import unspecified_argument, duplicate_instance

from ..features import Prepared, Fingerprinted


class BufferTransform:
	def transform(self, sample=None):
		return sample


class AbstractData(Prepared, Fingerprinted): # application of Prepared
	'''Includes mostly buffers and datasets, as well as batches and views (all of which uses prepare() and get())'''

	def copy(self):
		return duplicate_instance(self) # shallow copy
	# TODO: deepcopy


	def _update(self, sel=None, **kwargs):
		raise NotImplementedError


	def update(self, sel=None, **kwargs):
		if not self.is_ready:
			raise self.NotReady
		return self._update(sel=sel, **kwargs)


	def _fingerprint_data(self):
		return {'ready': self.is_ready, **super()._fingerprint_data()}


	def get(self, sel=None, **kwargs):
		try:
			return self._get(sel=sel, **kwargs)
		except self.NotReady:
			self.prepare()
			return self._get(sel=sel, **kwargs)


	def _get(self, sel=None, **kwargs):
		raise NotImplementedError


	class NoView(Exception):
		pass


	View = None
	def create_view(self, source=None, **kwargs):
		if self.View is None:
			raise self.NoView
		if source is None:
			source = self
		return self.View(source=source, **kwargs)


	def _title(self):
		raise NotImplementedError


	def __str__(self):
		return self._title()


	def __repr__(self):
		return str(self)



class AbstractView(AbstractData):
	_is_ready = True

	def __init__(self, source=None, sel=None, **kwargs):
		super().__init__(**kwargs)
		self.source = source
		self.sel = sel


	def _fingerprint_data(self):
		return {'source': self.fingerprint_obj(self.source), 'sel': self.fingerprint_obj(self.sel),
		        **super()._fingerprint_data()}


	View = None
	def create_view(self, source=None, **kwargs):
		if source is None:
			source = self
		if self.View is None:
			if self.source is None:
				raise self.NoSource
			return self.source.create_view(source=source, **kwargs)
		return super().create_view(source=source, **kwargs)


	def _merge_sel(self, sel=None):
		if self.sel is not None:
			sel = self.sel if sel is None else self.sel[sel]
		return sel


	@property
	def source(self):
		# if self._source is None:
		# 	raise self.NoSource
		return self._source
	@source.setter
	def source(self, source):
		if not self._check_source(source):
			raise self.InvalidSource(source)
		self._source = source


	def _check_source(self, source):
		return True


	class InvalidSource(Exception):
		def __init__(self, source):
			super().__init__(repr(source))
			self.source = source


	class NoSource(AbstractData.NotReady):
		pass


	@property
	def is_ready(self):
		return self.source is not None and self.source.is_ready


	def _prepare(self, *args, **kwargs):
		if self.source is None:
			raise self.NoSource
		return self.source.prepare(*args, **kwargs)


	def _update(self, sel=None, **kwargs):
		if self.source is None:
			raise self.NoSource
		sel = self._merge_sel(sel)
		return super()._update(sel=sel, **kwargs) # TODO: shouldnt this update source?


	def _get(self, sel=None, **kwargs):
		if self.source is None:
			raise self.NoSource
		sel = self._merge_sel(sel)
		return self.source.get(sel=sel, **kwargs)



class StorableUpdate(AbstractData):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._waiting_update = None


	def update(self, **kwargs):
		try:
			return super().update(**kwargs)
		except self.NotReady:
			self._waiting_update = self._store_update(**kwargs)


	def prepare(self, *args, **kwargs):
		out = super().prepare(*args, **kwargs)
		if self._waiting_update is not None:
			self._apply_update(self._waiting_update)
			self._waiting_update = None
		return out


	def _store_update(self, **kwargs):
		return kwargs


	def _apply_update(self, update):
		return self.update(**update)



class AbstractBuffer(BufferTransform, StorableUpdate, AbstractData):
	def __init__(self, space=None, **kwargs):
		super().__init__(**kwargs)
		self.space = space


	def _fingerprint_data(self):
		return {'space': self.fingerprint_obj(self.space), **super()._fingerprint_data()}


	@property
	def space(self):
		return self._space
	@space.setter
	def space(self, space):
		self._space = space





















