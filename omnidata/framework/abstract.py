from omnibelt import agnosticmethod



class Extractor:
	@agnosticmethod
	def extract(self, observation):
		raise NotImplementedError



class Encoder(Extractor):
	@agnosticmethod
	def extract(self, observation):
		return self.encode(observation)


	@agnosticmethod
	def encode(self, observation):
		raise NotImplementedError



class Decoder:
	@agnosticmethod
	def decode(self, latent):
		raise NotImplementedError



class Generator:
	@agnosticmethod
	def sample(self, *shape, gen=None):
		raise NotImplementedError



class Discriminator:
	@agnosticmethod
	def judge(self, observation):
		raise NotImplementedError



class Augmentation:
	@agnosticmethod
	def augment(self, observation):
		raise NotImplementedError



class Criterion:
	@agnosticmethod
	def compare(self, observation1, observation2):
		raise NotImplementedError



class Metric(Criterion): # obeys triangle inequality
	@agnosticmethod
	def distance(self, observation1, observation2):
		raise NotImplementedError


	@agnosticmethod
	def compare(self, observation1, observation2):
		return self.distance(observation1, observation2)



class PathCriterion(Criterion):
	@agnosticmethod
	def compare(self, observation1, observation2):
		return self.compare_path(observation1, observation2)


	@agnosticmethod
	def compare_path(self, path1, path2):
		raise NotImplementedError



class Interpolator: # returns N steps to get from start to finish ("evenly spaces", by default)
	@staticmethod
	def interpolate(start, end, N):
		raise NotImplementedError



class Estimator:
	@agnosticmethod
	def predict(self, observation):
		raise NotImplementedError



class Invertible:
	@agnosticmethod
	def forward(self, observation):
		raise NotImplementedError


	@agnosticmethod
	def inverse(self, observation):
		raise NotImplementedError



class Compressor:
	@staticmethod
	def compress(observation):
		raise NotImplementedError


	@staticmethod
	def decompress(data):
		raise NotImplementedError



class Quantizer:
	@staticmethod
	def quantize(observation): # generally "removes" noise
		raise NotImplementedError


	@staticmethod
	def dequantize(observation): # generally adds noise
		raise NotImplementedError


















