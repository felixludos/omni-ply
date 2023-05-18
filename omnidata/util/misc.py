import numpy as _np
# import torch as _torch


def deviced_fn(fn, device='cuda', out_device='cpu'):
	def _process_arg(t, d=device):
		if isinstance(t, _np.ndarray):
			t = _torch.as_tensor(t)
		if d is not None and isinstance(t, _torch.Tensor):
			t = t.to(d)
		return t
	def _wrapped(*args, **kwargs):
		args = list(map(_process_arg, args))
		kwargs = {key:_process_arg(val) for key, val in kwargs.items()}
		out = fn(*args, **kwargs)
		return _process_arg(out, d=out_device)
	return _wrapped



def combine_dims(tensor, start=1, end=None):
	if end is None:
		end = len(tensor.shape)
	combined_shape = [*tensor.shape[:start], -1, *tensor.shape[end:]]
	return tensor.view(*combined_shape)



def split_dim(tensor, *splits, dim=0):
	split_shape = [*tensor.shape[:dim], *splits, *tensor.shape[dim+1:]]
	return tensor.view(*split_shape)



def swap_dim(tensor, d1=0, d2=1):
	dims = list(range(len(tensor.shape)))
	dims[d1], dims[d2] = dims[d2], dims[d1]
	return tensor.permute(*dims)






