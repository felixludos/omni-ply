
from collections import OrderedDict
import torch
from omnibelt import unspecified_argument, duplicate_instance

from .random import Seeded
from .features import Device, DeviceContainer, Prepared, Fingerprinted
from .exporting import Exporter



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



class Function(Fingerprinted):
	din, dout = None, None

	def __init__(self, *args, din=unspecified_argument, dout=unspecified_argument, **kwargs):
		super().__init__(*args, **kwargs)
		if din is not unspecified_argument:
			self.din = din
		if dout is not unspecified_argument:
			self.dout = dout
		# self.din, self.dout = din, dout

	
	def get_dims(self):
		return self.din, self.dout


	def _fingerprint_data(self):
		data = super()._fingerprint_data()
		data['din'] = self.fingerprint_obj(self.din)
		data['dout'] = self.fingerprint_obj(self.dout)
		if self.din is not None:
			x = self.din.sample(4, gen=torch.Generator().manual_seed(16283393149723337453))
			try:
				with torch.no_grad():
					y = self(x)
				data['output'] = self.fingerprint_obj(y)
			except:
				raise # TESTING
		return data


	# def __call__(self, *args, **kwargs):
	# 	raise NotImplementedError
	


class Container(OrderedDict): # TODO: instead of inheriting from OrderedDict use Mapping (maybe?)
							  # http://www.kr41.net/2016/03-23-dont_inherit_python_builtin_dict_type.html
	def _find_missing(self, key):
		raise KeyError(key)


	class _missing: # flag for missing items
		pass


	def __getitem__(self, item):
		try:
			return super().__getitem__(item)
		except KeyError:
			return self._find_missing(item)
			# self[item] = val
			# return val


	# def export(self):
	# 	raise NotImplementedError


	def __str__(self):
		entries = ', '.join(self.keys())
		return f'{self.__class__.__name__}({entries})'


	def __repr__(self):
		return str(self)



class DevicedContainer(Device, Container):
	def _to(self, device, **kwargs):
		for key, val in self.items():
			if isinstance(val, (Device, torch.Tensor)):
				self[key] = val.to(device)




# class TensorContainer(Device):
#
# 	def _item_iterator(self):
# 		raise NotImplementedError
#
#
# 	def _update_payload(self, updates):
# 		for key, content in updates.items():
# 			self[key] = content
#
#
# 	def _to(self, device, **kwargs):
# 		updates = {key: content.to(device) for key, content in self._item_iterator()}
# 		self._update_payload(updates)
#
#
# 	def __str__(self):
# 		return f'{self.__class__.__name__}({self._str_info()})'
#
#
#
# class TensorList(TensorContainer, list):
# 	def _str_info(self):
# 		num = len(self)
# 		msg = 'item' if num == 1 else 'items'
# 		return f'{num} {msg}'
#
#
# 	def _item_iterator(self):
# 		return enumerate(self)
#
#
#
# class TensorDict(TensorContainer, dict):
# 	def _str_info(self):
# 		msg = ', '.join(self.keys())
# 		return msg
#
#
# 	def _item_iterator(self):
# 		return self.items()









