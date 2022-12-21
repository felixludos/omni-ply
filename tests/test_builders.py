import sys, os
import yaml

import torch
from torch import nn

from omnibelt import unspecified_argument, agnostic
import omnifig as fig

import omnidata as od
from omnidata import toy
from omnidata import Builder, Buildable, RegistryBuilder, ClassBuilder, MultiBuilder
from omnidata import hparam, inherit_hparams, machine, spaces

def _cmp_dicts(d1, d2):
	return yaml.dump(d1, sort_keys=True) == yaml.dump(d2, sort_keys=True)



class Activation(RegistryBuilder, default_ident='relu', products={
							'relu': nn.ReLU,
							'prelu': nn.PReLU,
							'lrelu': nn.LeakyReLU,
							'tanh': nn.Tanh,
							'softplus': nn.Softplus,
							'sigmoid': nn.Sigmoid,
							'elu': nn.ELU,
							'selu': nn.SELU,
                         }):
	inplace = hparam(True, space=spaces.Binary())

	@agnostic
	def build(self, ident, inplace, **kwargs):
		product = self.product(ident=ident, inplace=inplace, **kwargs)
		if product in {nn.ELU, nn.ReLU, nn.SELU}:
			return product(inplace=inplace)
		return product()



# def test_reg_builder():
# 	nonlin = Activation.build('relu')
# 	assert isinstance(nonlin, nn.ReLU)
# 	assert nonlin.inplace is True
#
# 	nonlin = Activation.build('relu', inplace=False)
# 	assert nonlin.inplace is False
#
# 	nonlin = Activation.build('sigmoid')
# 	assert isinstance(nonlin, nn.Sigmoid)
#
# 	nonlin = Activation.validate('elu')
# 	assert isinstance(nonlin, nn.ELU)
#
# 	nonlin = Activation.product('tanh')
# 	assert nonlin is nn.Tanh
#
# 	assert len(Activation.available_products()) == 8

class Negative(nn.Module):
	def forward(self, x):
		return -super().forward(x)


import inspect

def test_mod_product():

	b1 = Activation('elu')
	b2 = Activation()

	assert b1 is not b2
	assert b1.ident == 'elu'
	assert b2.ident == 'relu'

	assert b1.product() is nn.ELU
	assert b2.product() is nn.ReLU
	assert isinstance(b1.build(), nn.ELU)
	assert isinstance(b2.build(), nn.ReLU)
	assert b2.product('tanh') is nn.Tanh

	assert len(list(b1.mods())) == 0
	assert len(list(Activation.mods())) == 0
	b1.modded(Negative)
	assert len(list(b1.mods())) == 1
	assert len(list(Activation.mods())) == 0

	b1.vanilla()
	assert len(list(b1.mods())) == 0
	assert len(list(Activation.mods())) == 0

	nonlin = b1.build('relu')
	assert nonlin(torch.as_tensor(10)) == 10

	nonlin = b1.modded(Negative).build('relu')
	assert isinstance(nonlin, Negative)

	assert nonlin.__class__.__name__ == 'Negative_ReLU'
	assert nonlin(torch.as_tensor(10)) == -10

	nonlin = b1.vanilla().build('relu')
	assert nonlin(torch.as_tensor(10)) == 10



class MyModels(ClassBuilder, nn.Module):
	p1 = hparam(required=True)
	p2 = hparam(10)
	p3 = hparam('hello', inherit=True)
	p4 = hparam((1,2,3), hidden=True)


class ModelA(MyModels, ident='a'):
	p2 = hparam(20)

@inherit_hparams('p1', 'p2')
class ModelB(MyModels, ident='b'):
	pass

@inherit_hparams('p1', 'p2')
class ModelC(MyModels, ident='c'):
	pass


class ModelD(MyModels, ident='d'):
	pass


def test_param_product():



	pass





