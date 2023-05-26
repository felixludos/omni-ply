import sys, os
import yaml

# import torch
# from torch import nn

from omnibelt import unspecified_argument, agnostic
import omnifig as fig

import omniplex as od
from omniplex import toy
from omniplex import Builder, RegistryBuilder, RegisteredProduct, MatchingBuilder
from omniplex import hparam, inherit_hparams, submodule, spaces



def _cmp_dicts(d1, d2):
	return yaml.dump(d1, sort_keys=True) == yaml.dump(d2, sort_keys=True)



class Activation(RegistryBuilder, default_ident='relu', products={
							# 'relu': nn.ReLU,
							# 'prelu': nn.PReLU,
							# 'lrelu': nn.LeakyReLU,
							# 'tanh': nn.Tanh,
							# 'softplus': nn.Softplus,
							# 'sigmoid': nn.Sigmoid,
							# 'elu': nn.ELU,
							# 'selu': nn.SELU,
                         }):
	inplace = hparam(True, space=spaces.Binary(), hidden=True)


	def _build_kwargs(self, product, ident, **kwargs):
		kwargs = super()._build_kwargs(product, ident, **kwargs)
		if issubclass(product, (nn.ELU, nn.ReLU, nn.SELU)) and 'inplace' not in kwargs:
			kwargs['inplace'] = self.inplace
		return kwargs



def test_reg_builder():
	builder = Activation()
	nonlin = builder.build('relu')
	assert isinstance(nonlin, nn.ReLU)
	assert nonlin.inplace is True

	nonlin = Activation().build('relu', inplace=False)
	assert nonlin.inplace is False

	nonlin = Activation().build('sigmoid')
	assert isinstance(nonlin, nn.Sigmoid)

	nonlin = Activation().validate('elu')
	assert isinstance(nonlin, nn.ELU)

	nonlin = Activation().product('tanh')
	assert nonlin is nn.Tanh

	assert len(list(Activation().products())) == 8



class Negative():#(nn.Module):
	def forward(self, x):
		return -super().forward(x)



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
	assert len(list(Activation().mods())) == 0
	b1.modded(Negative)
	assert len(list(b1.mods())) == 1
	assert len(list(Activation().mods())) == 0

	b1.vanilla()
	assert len(list(b1.mods())) == 0
	assert len(list(Activation().mods())) == 0

	nonlin = b1.build('relu')
	assert nonlin(torch.as_tensor(10)) == 10

	nonlin = b1.modded(Negative).build('relu')
	assert isinstance(nonlin, Negative)

	assert nonlin.__class__.__name__ == 'Negative_ReLU'
	assert nonlin(torch.as_tensor(10)) == -10

	nonlin = b1.vanilla().build('relu')
	assert nonlin(torch.as_tensor(10)) == 10



# class MyModels(RegistryBuilder, nn.Module, default_ident='b'):
class MyModels(RegistryBuilder, default_ident='b'):
	p1 = hparam(required=True)
	p2 = hparam(10)
	p3 = hparam('hello', inherit=True)
	p4 = hparam((1,2,3), hidden=True)


class ModelA(RegisteredProduct, registry=MyModels, ident='a'):
	p2 = hparam(20)


class ModelB(RegisteredProduct, registry=MyModels, ident='b'):
	p1 = hparam(required=True)
	p2 = hparam(10)


class ModelC(RegisteredProduct, registry=MyModels, ident='c'):
	p1 = hparam(required=True)
	p2 = hparam(10)


class ModelD(RegisteredProduct, registry=MyModels, ident='d'):
	p1 = hparam(required=True)
	p2 = hparam(10)



def test_param_product():

	assert len(list(MyModels().products())) == 4

	hparams = dict(MyModels().named_hyperparameters())
	assert len(hparams) == 4
	assert tuple(sorted(hparams.keys())) == ('ident', 'p1', 'p2', 'p3') # p4 is hidden
	assert len(list(MyModels().named_hyperparameters(hidden=True))) == 7

	assert hparams['p1'] is MyModels().get_hparam('p1')

	assert MyModels().p2 == 10
	assert ModelA().p2 == 20
	assert MyModels().product('a')().p2 == 20
	builder = MyModels()
	assert builder.p2 == 10
	assert ModelA().p2 == 20
	assert builder.build('a').p2 == 10
	# assert ModelA().build().p2 == 20

	a = ModelA(p2=50)
	# assert a.build().p2 == 20
	# assert a.build(p2=50).p2 == 50
	# assert a.build_replica().p2 == 50

	assert isinstance(ModelA(), ModelA)
	# assert isinstance(ModelA().build(), ModelA)
	assert isinstance(builder.build('a'), ModelA)

	assert builder.build('b').p2 == 10
	assert builder.build('d').p2 == 10

	a = MyModels().build('a', p2=100)

	assert MyModels().p2 == 10
	assert ModelA().p2 == 20
	assert a.p2 == 100

	builder = MyModels(p2=50) # TODO

	assert MyModels().p2 == 10
	assert builder.p2 == 50
	b = builder.build()
	assert b.p2 == 50
	assert isinstance(b, ModelB)

	a = builder.build('a')
	assert a.p2 == 50
	assert isinstance(a, ModelA)



# def test_spec():
#
# 	a = ModelA(p2=50)
#
# 	spec = a.spec().prepare()
#
# 	assert len(spec) == len(list(a.named_hyperparameters()))







