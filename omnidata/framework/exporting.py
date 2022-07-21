from omnibelt import agnosticmethod
from omnibelt import Exporter as _Old_Exporter#, export, load_export
from omnibelt import exporting_common as _common

from .features import Rooted

# TODO: separate Exportable (custom export function) and Exporter (maybe?)

class Exporter(_Old_Exporter, Rooted, create_table=True):
	@agnosticmethod
	def create_export_path(self, name, root=None, ext=None):
		if root is None:
			root = self.get_root()
		return super().create_export_path(name, root=root, ext=ext)
	
	
	@agnosticmethod
	def create_load_path(self, name, root=None):
		if root is None:
			root = self.get_root()
		return super().create_load_path(name, root=root)



def export(obj, name=None, root=None, fmt=None, path=None, **kwargs):
	return Exporter.export(obj, name=name, root=root, fmt=fmt, path=path, **kwargs)



def load_export(name=None, root=None, fmt=None, path=None, **kwargs):
	return Exporter.load_export(name=name, root=root, fmt=fmt, path=path, **kwargs)



# TODO: describe this section: replacing the default functionality (which requires manually including the root),
#  to automatically "infer" the root. This involves replacing the old classes with modified children.

_update_fmts = {}
for fmt in _Old_Exporter._export_fmts_head:
	if fmt not in _update_fmts:
		_update_fmts[fmt] = type(fmt.__name__, (fmt, Exporter), {})
for fmt in _Old_Exporter._export_fmts_tail:
	if fmt not in _update_fmts:
		_update_fmts[fmt] = type(fmt.__name__, (fmt, Exporter), {})
for typ, fmt in _Old_Exporter._export_fmt_types.items():
	if fmt not in _update_fmts:
		_update_fmts[fmt] = type(fmt.__name__, (fmt, Exporter), {})
for ext, fmt in _Old_Exporter._export_fmt_exts.items():
	if fmt not in _update_fmts:
		_update_fmts[fmt] = type(fmt.__name__, (fmt, Exporter), {})
Exporter._export_fmts_head = [_update_fmts[fmt] for fmt in _Old_Exporter._export_fmts_head]
Exporter._export_fmts_tail = [_update_fmts[fmt] for fmt in _Old_Exporter._export_fmts_tail]
Exporter._export_fmt_types = {typ: _update_fmts[fmt] for typ, fmt in _Old_Exporter._export_fmt_types.items()}
Exporter._export_fmt_exts = {ext: _update_fmts[fmt] for ext, fmt in _Old_Exporter._export_fmt_exts.items()}
del _update_fmts



import numpy as np
import pandas as pd
import h5py as hf
import torch
from PIL import Image



class NumpyExport(Exporter, extensions='.npy'):
	@staticmethod
	def validate_export_obj(obj, **kwargs):
		return isinstance(obj, np.ndarray)
	@staticmethod
	def _load_export(path, src=None, **kwargs):
		return np.load(path, **kwargs)
	@staticmethod
	def _export_self(self, path, src=None, **kwargs):
		return np.save(path, self, **kwargs)



class NpzExport(Exporter, extensions='.npz'):
	@staticmethod
	def _load_export(path, src=None, auto_load=False, **kwargs):
		obj = np.load(path, **kwargs)
		if auto_load:
			return {key: obj[key] for key in obj.keys()}
		return obj
	@staticmethod
	def _export_self(self, path, src=None):
		args, kwargs = ([], self) if isinstance(self, dict) else (self, {})
		return np.savez(path, *args, **kwargs)



class PandasExport(Exporter, extensions='.csv', types=pd.DataFrame):
	@staticmethod
	def _load_export(path, src=None, **kwargs):
		return pd.read_csv(path, **kwargs)
	@staticmethod
	def _export_self(self, path, src=None, **kwargs):
		return self.to_csv(path, **kwargs)
	
	

class ImageExport(Exporter, extensions='.png'):
	@staticmethod
	def validate_export_obj(obj, **kwargs):
		return isinstance(obj, Image.Image)
	@staticmethod
	def _load_export(path, src=None, **kwargs):
		return Image.open(path, **kwargs)
	@staticmethod
	def _export_self(self, path, src=None, **kwargs):
		return self.save(path, **kwargs)



class NumpyImageExport(ImageExport, extensions='.png'):
	@staticmethod
	def _export_self(self, path, src=None, **kwargs):
		if not isinstance(self, Image.Image):
			if self.dtype != np.uint8:
				raise NotImplementedError
			if len(self.shape) == 3:
				if self.shape[0] in {1, 3, 4} and self.shape[2] not in {1, 3, 4}:
					self = self.transpose(1, 2, 0)
				if self.shape[2] == 1:
					self = self.reshape(*self.shape[:2])
			self = Image.fromarray(self)
		return super()._export_self(self, path, src=src, **kwargs)



class JpgExport(ImageExport, extensions='.jpg'):
	pass



class HDFExport(Exporter, extensions=['.h5', '.hf', '.hdf']):
	@staticmethod
	def _load_export(path, src=None, auto_load=False, mode='r', **kwargs):
		f = hf.File(str(path), mode=mode, **kwargs)
		if auto_load:
			obj = {k: f[k][()] for k in f.keys()}
			f.close()
		else:
			obj = f
		return obj
	@staticmethod
	def _export_self(self, path, src=None, mode='a', meta=None, **kwargs):
		with hf.File(str(path), mode=mode, **kwargs) as f:
			if meta is not None:
				for k, v in meta.items():
					f.attrs[k] = v
			for k, v in self.items():
				f.create_dataset(name=k, data=v)
		return path



class DictExport(Exporter, extensions='', types=dict):
	@staticmethod
	def validate_export_obj(obj, **kwargs):
		return isinstance(obj, dict) and all(isinstance(key, str) for key in obj)
	@staticmethod
	def _load_export(path, src, **kwargs):
		return {item.stem: src.load_export(path=item) for item in path.glob('*')}
	@staticmethod
	def _export_self(self, path, src, **kwargs):
		path.mkdir(exist_ok=True)
		for key, val in self.items():
			src.export(val, name=key, root=path)
		return path



class PytorchExport(Exporter, extensions=['.pt', '.pth.tar']):
	@staticmethod
	def validate_export_obj(obj, **kwargs):
		return True
	@staticmethod
	def _load_export(path, src=None, **kwargs):
		return torch.load(path, **kwargs)
	@staticmethod
	def _export_self(self, path, src=None, **kwargs):
		return torch.save(self, path, **kwargs)
Exporter._export_fmts_tail.remove(PytorchExport)
Exporter._export_fmts_tail.insert(1, PytorchExport)



