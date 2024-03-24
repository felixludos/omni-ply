import torch as _torch
from .features import Device as _Device

# TODO: separate with defaults
from omniplex.framework.common import \
	Extractor as _Extractor, \
	Encoder as _Encoder, \
	Decoder as _Decoder, \
	Generator as _Generator, \
	Discriminator as _Discriminator, \
	Augmentation as _Augmentation, \
	Criterion as _Criterion, \
	Metric as _Metric, \
	PathCriterion as _PathCriterion, \
	Interpolator as _Interpolator, \
	Estimator as _Estimator, \
	Invertible as _Invertible, \
	Compressor as _Compressor, \
	Quantizer as _Quantizer, \
	Function as _Function



class _ImplicitModel(_Function, _Device):
	def __init__(self, fn, din_device=None, dout_device=None, **kwargs):
		super().__init__(**kwargs)
		self.fn = fn
		self.din_device = din_device
		self.dout_device = dout_device


	def _wrapped_call(self, *args):
		return self._process_output(self.fn(*map(self._process_input, args)))


	def _process_input(self, inp):
		device = self.din_device
		if device is None:
			device = self.device
		if device is not None and isinstance(inp, (_torch.Tensor, _Device)):
			inp = inp.to(device)
		return inp


	def _process_output(self, out):
		device = self.dout_device
		if device is None:
			device = self.device
		if device is not None and isinstance(out, (_torch.Tensor, _Device)):
			out = out.to(device)
		return out



class _ImplicitInvertibleModel(_ImplicitModel):
	def __init__(self, fn, ifn=None, **kwargs):
		super().__init__(fn, **kwargs)
		self.ifn = ifn


	def _wrapped_inv_call(self, *args):
		return self._process_output(self.fn(*map(self._process_input, args)))



class Extractor(_Extractor, _ImplicitModel):
	def extract(self, observation):
		return self._wrapped_call(observation)



class Encoder(_Encoder, Extractor):
	def encode(self, observation):
		return self._wrapped_call(observation)



class Decoder(_Decoder, _ImplicitModel):
	def decode(self, latent):
		return self._wrapped_call(latent)



class Generator(_Generator, _ImplicitModel):
	def sample(self, *shape, gen=None):
		return self._process_output(self.fn(*shape, gen=gen))



class Discriminator(_Discriminator, _ImplicitModel):
	def judge(self, observation):
		return self._wrapped_call(observation)



class Criterion(_Criterion, _ImplicitModel):
	def compare(self, observation1, observation2):
		return self._wrapped_call(observation1, observation2)



class Metric(_Metric, Criterion): # obeys triangle inequality
	def distance(self, observation1, observation2):
		return self._wrapped_call(observation1, observation2)



class Interpolator(_Interpolator, _ImplicitModel):
	def interpolate(self, start, end, N):
		return self._process_output(self.fn(self._process_input(start), self._process_input(end), N))



class Estimator(_Estimator, _ImplicitModel):
	def predict(self, observation):
		return self._wrapped_call(observation)



class Augmentation(_Augmentation, _ImplicitModel):
	def augment(self, observation):
		return self._wrapped_call(observation)



class PathCriterion(_PathCriterion, Criterion):
	def compare_path(self, path1, path2):
		return self._wrapped_call(path1, path2)



class Invertible(_Invertible, _ImplicitInvertibleModel):
	def forward(self, observation):
		return self._wrapped_call(observation)


	def inverse(self, observation):
		return self._wrapped_inv_call(observation)



class Compressor(_Compressor, _ImplicitInvertibleModel):
	def compress(self, observation):
		return self.fn(self._process_input(observation))


	def decompress(self, data):
		return self._process_output(self.ifn(data))



class Quantizer(_Quantizer, _ImplicitInvertibleModel):
	def quantize(self, observation):
		return self._wrapped_call(observation)


	def dequantize(self, observation):
		return self._wrapped_inv_call(observation)









