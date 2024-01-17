from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Type, Iterable, Iterator
from pathlib import Path
from omnibelt import agnosticmethod
from omnibelt.exporting import ExportManager, Exporter, Exportable, export, load_export
from omnibelt import exporting_common as _exporting_common

import numpy as np
import pandas as pd
# import h5py as hf
# import torch
# from PIL import Image

from .filesystem import Rooted


class NumpyExport(Exporter, extensions='.npy'):
	@staticmethod
	def validate_export_obj(obj: Any) -> bool:
		return isinstance(obj, np.ndarray)
	@staticmethod
	def _load_export(path: Path, src: Type['ExportManager'], **kwargs) -> Any:
		return np.load(path, **kwargs)
	@staticmethod
	def _export_self(payload: Any, path: Path, src: Type['ExportManager'], **kwargs) -> Optional[Path]:
		return np.save(path, payload, **kwargs)



class NpzExport(Exporter, extensions='.npz'):
	@staticmethod
	def _load_export(path: Path, src: Type['ExportManager'], auto_load=False, **kwargs) -> Any:
		obj = np.load(path, **kwargs)
		if auto_load:
			return {key: obj[key] for key in obj.keys()}
		return obj
	@staticmethod
	def _export_payload(payload: Any, path: Path, src: Type['ExportManager']) -> Optional[Path]:
		args, kwargs = ([], payload) if isinstance(payload, dict) else (payload, {})
		return np.savez(path, *args, **kwargs)



class PandasExport(Exporter, extensions='.csv', types=pd.DataFrame):
	@staticmethod
	def _load_export(path: Path, src: Type['ExportManager'], **kwargs) -> Any:
		return pd.read_csv(path, **kwargs)
	@staticmethod
	def _export_payload(payload: Any, path: Path, src: Type['ExportManager'], **kwargs) -> Optional[Path]:
		return payload.to_csv(path, **kwargs)
	
	

class ImageExport(Exporter, extensions='.png'):
	@staticmethod
	def validate_export_obj(obj, **kwargs):
		return isinstance(obj, Image.Image)
	@staticmethod
	def _load_export(path: Path, src: Type['ExportManager'], **kwargs) -> Any:
		return Image.open(path, **kwargs)
	@staticmethod
	def _export_payload(payload: Any, path: Path, src: Type['ExportManager'], **kwargs) -> Optional[Path]:
		return payload.save(path, **kwargs)



class NumpyImageExport(ImageExport, extensions='.png'):
	@staticmethod
	def _export_payload(payload: Any, path: Path, src: Type['ExportManager'], **kwargs) -> Optional[Path]:
		if not isinstance(payload, Image.Image):
			if payload.dtype != np.uint8:
				raise NotImplementedError
			if len(payload.shape) == 3:
				if payload.shape[0] in {1, 3, 4} and payload.shape[2] not in {1, 3, 4}:
					payload = payload.transpose(1, 2, 0)
				if payload.shape[2] == 1:
					payload = payload.reshape(*payload.shape[:2])
			payload = Image.fromarray(payload)
		return super()._export_self(payload, path, src=src, **kwargs)



class JpgExport(ImageExport, extensions='.jpg'):
	pass



class HDFExport(Exporter, extensions=['.h5', '.hf', '.hdf']):
	@staticmethod
	def _load_export(path: Path, src: Type['ExportManager'], *, auto_load=False, mode='r', **kwargs) -> Any:
		f = hf.File(str(path), mode=mode, **kwargs)
		if auto_load:
			obj = {k: f[k][()] for k in f.keys()}
			f.close()
		else:
			obj = f
		return obj
	@staticmethod
	def _export_payload(payload: Any, path: Path, src: Type['ExportManager'], *,
	                    mode='a', meta=None, **kwargs) -> Optional[Path]:
		with hf.File(str(path), mode=mode, **kwargs) as f:
			if meta is not None:
				for k, v in meta.items():
					f.attrs[k] = v
			for k, v in payload.items():
				f.create_dataset(name=k, data=v)
		return path



class DictExport(Exporter, extensions='', types=dict):
	@staticmethod
	def validate_export_obj(obj, **kwargs):
		return isinstance(obj, dict) and all(isinstance(key, str) for key in obj)
	@staticmethod
	def _load_export(path: Path, src: Type['ExportManager']) -> Any:
		return {item.stem: src.load_export(path=item) for item in path.glob('*')}
	@staticmethod
	def _export_payload(payload: Any, path: Path, src: Type['ExportManager']) -> Optional[Path]:
		path.mkdir(exist_ok=True)
		for key, val in payload.items():
			src.export(val, name=key, root=path)
		return path



class PytorchExport(Exporter, extensions=['.pt', '.pth.tar'], head=True):
	@staticmethod
	def validate_export_obj(obj, **kwargs):
		return True
	@staticmethod
	def _load_export(path: Path, src: Type['ExportManager'], **kwargs) -> Any:
		return torch.load(path, **kwargs)
	@staticmethod
	def _export_payload(payload: Any, path: Path, src: Type['ExportManager'], **kwargs) -> Optional[Path]:
		return torch.save(payload, path, **kwargs)



