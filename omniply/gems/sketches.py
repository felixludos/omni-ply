
# class Equivariance(Structured):
# 	A = submodule(None, inherit=True)(output='Ax')(input='x')
# 	B = submodule(final=True)(output='Bx')(input='x')
#
# 	metric = building.metric('mse')(output='loss')(input='ABx', target='BAx')
#
# 	def __init__(self, **kwargs):
# 		super().__init__(**kwargs)
# 		# self.include(Mechanism(self.A, external=dict(output=self.gap('ABx')), internal=dict(input=self.gap('Bx'))))
# 		# self.include(Mechanism(self.B, external=dict(output=self.gap('BAx')), internal=dict(input=self.gap('Ax'))))
# 		self.include(Mechanism(self.A)(output=self.gap('ABx'), input=self.gap('Bx')))
# 		self.include(Mechanism(self.B)(output=self.gap('BAx'), input=self.gap('Ax')))



# class Equivariance2(Structured):
# 	A = submodule(None, inherit=True)(output='Ax')(input='x')(submodule()(output='ABx')(input='Bx'))
# 	B = submodule(final=True)(output='Bx')(input='x')(submodule()(output='BAx')(input='Ax'))
#
# 	metric = building.metric('mse')(output='loss')(input='ABx', target='BAx')



class Equivariance3(Structured):
	@submodule(inherit=True)(output='Ax', input='x')
	@submodule()(output='ABx', input='Bx')
	def A(self): raise self._ResolveError

	@submodule(final=True)(output='Bx', input='x')
	@submodule()(output='BAx', input='Ax')
	def B(self): raise self._ResolveError

	metric = part.metric('mse')(output='loss', input='ABx', target='BAx')


class Equivariance4(Structured):
	A = submodule(inherit=True)(output='Ax', input='x')(submodule()(output='ABx', input='Bx'))
	B = submodule(final=True)(output='Bx', input='x')(submodule()(output='BAx', input='Ax'))

	metric = part.metric('mse')(output='loss', input='ABx', target='BAx')



# part = prior_art (!)

@part.metric.register('mse')
@tool('output')
def mse(input, target):
	return torch.mean((input - target) ** 2)


@art.metric.register('mse')
class MSE(Structured):
	wts = hparam(None)
	aggregate = hparam(True)

	@tool('output')
	def forward(self, input, target):
		full = (input - target) ** 2
		if self.wts is not None:
			full = full * self.wts
		if self.aggregate:
			return torch.mean(full)
		return full

	@forward.space
	def output_space(self, input=None, target=None):
		if input is not None and target is not None and input.shape() != target.shape():
			raise ValueError(f'input and target shapes do not match: {input.shape()} != {target.shape()}')
		return spaces.Scalar(batched=self.aggregate is None) if self.aggregate else spaces.Tensor.of(input, lower_bound=0.0)


def autobuilder(raw: Union[str, tuple[str, dict[str,Any]], dict[str,Any]]):
	if isinstance(raw, str):
		return building.metric(raw)
	if isinstance(raw, dict):
		return building.metric(**raw)
	# check if raw is iterable allowing lists or generators
	if isinstance(raw, Iterable):
		raw = tuple(raw)
		if len(raw) == 2:
			name, kwargs = raw
			if isinstance(kwargs, dict):
				return building.metric(name, **kwargs)
	raise ValueError(f'Invalid autobuilder input: {raw}')



