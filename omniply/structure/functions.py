from omnibelt import unspecified_argument

from ..persistent import Fingerprinted



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


	def __call__(self, inp):
		return self.forward(inp)


	# def forward(self, inp):
	# 	raise NotImplementedError


	def _fingerprint_data(self):
		data = super()._fingerprint_data()
		data['din'] = self.din
		data['dout'] = self.dout
		# if self.din is not None:
		# 	x = self.din.sample(4, gen=torch.Generator().manual_seed(16283393149723337453))
		# 	try:
		# 		with torch.no_grad():
		# 			y = self(x)
		# 		data['output'] = extractor.extract_data(y)
		# 	except:
		# 		raise # TESTING
		return data













