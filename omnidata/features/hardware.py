import sys
from omnibelt import unspecified_argument


class SharableAttrs:
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._shared_attrs = set()


	def _make_shared(self, key, val=unspecified_argument):
		if val is unspecified_argument:
			val = getattr(self, key)
		self._shared_attrs.add(key)
		setattr(self, key, [val])


	def access_shared(self, key):
		val = getattr(self, key, None)
		if val is not None and key in self._shared_attrs:
			return val[0]
		return val



if 'torch' in sys.modules:
	import torch
	_default_device = 'cuda' if torch.cuda.is_available() else 'cpu'
else:
	_default_device = 'cpu'



class Device:
	def __init__(self, *args, device=_default_device, **kwargs):
		super().__init__(*args, **kwargs)
		self.device = device


	def to(self, device, **kwargs):
		self.device = device
		out = self._to(device, **kwargs)
		if out is not None:
			return out
		return self


	def _to(self, device, **kwargs):
		raise NotImplementedError



class DeviceContainer(Device):
	def __init__(self, *, children=None, **kwargs):
		if children is None:
			children = {}
		super().__init__(**kwargs)
		self._device_children = set()
		self._register_deviced_children(**children)


	def _register_deviced_children(self, **children):
		for name, child in children.items():
			self._device_children.add(name)
			setattr(self, name, child)


	def _to(self, device, **kwargs):
		children = {}
		for name in self._device_children:
			obj = getattr(self, name, None)
			if obj is not None:
				children[name] = obj.to(device)
		self._register_deviced_children(**children)







