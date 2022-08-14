

import torch
from torch import nn

from torch import optim



class Optimizer: # TODO: make this exportable
	def __init__(self, A=None, **settings):
		super().__init__(params=[torch.zeros(0)], **settings)
		self.param_groups.clear()
	
	def __setstate__(self, state):
		groups = state.get('param_groups', None)
		if groups is not None:
			for group, new in zip(self.param_groups, groups):
				group.update({k:v for k,v in new.items() if not isinstance(v, LoadedValue)})
			del state['param_groups']
		super().__setstate__(state)
	
	def prep(self, params):
		
		param_groups = list(params)
		if len(param_groups) == 0:
			raise ValueError("optimizer got an empty parameter list")
		if not isinstance(param_groups[0], dict):
			param_groups = [{'params': param_groups}]
		
		for param_group in param_groups:
			self.add_param_group(param_group)



	pass


@fig.AutoComponent('sgd', auto_name=False)
class SGD(OptimizerBase, O.SGD):
	def __init__(self, lr, momentum=0, dampening=0, weight_decay=0, nesterov=False):
		super().__init__(lr=lr, momentum=momentum, dampening=dampening, weight_decay=weight_decay, nesterov=nesterov)


@fig.AutoComponent('asgd', auto_name=False)
class ASGD(OptimizerBase, O.ASGD):
	def __init__(self, lr=0.01, lambd=0.0001, alpha=0.75, t0=1000000.0, weight_decay=0):
		super().__init__(lr=lr, lambd=lambd, alpha=alpha, t0=t0, weight_decay=weight_decay)


@fig.AutoComponent('adadelta', auto_name=False)
class Adadelta(OptimizerBase, O.Adadelta):
	def __init__(self, lr=1.0, rho=0.9, eps=1e-06, weight_decay=0):
		super().__init__(lr=lr, rho=rho, weight_decay=weight_decay, eps=eps)


@fig.AutoComponent('adagrad', auto_name=False)
class Adagrad(OptimizerBase, O.Adagrad):
	def __init__(self, lr=0.01, lr_decay=0, weight_decay=0, initial_accumulator_value=0, eps=1e-10):
		super().__init__(lr=lr, lr_decay=lr_decay, weight_decay=weight_decay,
		                 initial_accumulator_value=initial_accumulator_value, eps=eps)


@fig.AutoComponent('adam', auto_name=False)
class Adam(OptimizerBase, O.Adam):
	def __init__(self, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8, weight_decay=0, amsgrad=False):
		super().__init__(lr=lr, betas=(beta1, beta2), eps=eps, weight_decay=weight_decay, amsgrad=amsgrad)


@fig.AutoComponent('adamw', auto_name=False)
class AdamW(OptimizerBase, O.AdamW):
	def __init__(self, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8, weight_decay=1e-2, amsgrad=False):
		super().__init__(lr=lr, betas=(beta1, beta2), eps=eps, weight_decay=weight_decay, amsgrad=amsgrad)


@fig.AutoComponent('adamax', auto_name=False)
class Adamax(OptimizerBase, O.Adamax):
	def __init__(self, lr=0.002, beta1=0.9, beta2=0.999, eps=1e-08, weight_decay=0):
		super().__init__(lr=lr, betas=(beta1, beta2), eps=eps, weight_decay=weight_decay)


@fig.AutoComponent('rmsprop', auto_name=False)
class RMSprop(OptimizerBase, O.RMSprop):
	def __init__(self, lr=0.01, alpha=0.99, eps=1e-08, weight_decay=0, momentum=0, centered=False):
		super().__init__(lr=lr, alpha=alpha, eps=eps, weight_decay=weight_decay, momentum=momentum, centered=centered)


@fig.AutoComponent('rprop', auto_name=False)
class Rprop(OptimizerBase, O.Rprop):
	def __init__(self, lr=0.01, eta1=0.5, eta2=1.2, step1=1e-06, step2=50):
		super().__init__(lr=lr, etas=(eta1, eta2), step_sizes=(step1, step2))


try:
	from ranger import Ranger as RangerOptim
	
	
	@fig.AutoComponent('ranger', auto_name=False)
	class Ranger(OptimizerBase, RangerOptim):
		def __init__(self, lr=0.001, alpha=0.5, k=6, N_sma_threshhold=5, beta1=.95, beta2=0.999, eps=1e-5,
		             weight_decay=0):
			super().__init__(lr=lr, alpha=alpha, k=k, N_sma_threshhold=N_sma_threshhold, betas=(beta1, beta2),
			                 eps=eps, weight_decay=weight_decay)

except ImportError:
	prt.info('failed to import Ranger optimizer')













