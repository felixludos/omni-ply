
import sys, os
import yaml

import torch
from torch import nn

from omnibelt import unspecified_argument, agnostic
import omnifig as fig

import omnidata as od
from omnidata import toy
from omnidata import Builder, Buildable, HierarchyBuilder, RegisteredProduct, MatchingBuilder, RegistryBuilder, \
	register_builder, get_builder
from omnidata import BudgetLoader
from omnidata import hparam, inherit_hparams, submodule, submachine, spaces
from omnidata import Guru, Context, material, space, indicator, machine, Structured

from omnidata import Spec, Builder, Buildable, InitWall
from omnidata import toy



class LVM(Structured, InitWall, nn.Module):
	latent_dim = hparam(required=True, inherit=True)

	@space('latent')
	def latent_space(self):
		return spaces.Unbound(self.latent_dim)



class AE(LVM):
	encoder = submachine(builder='encoder', application=dict(input='observation', output='latent'))
	decoder = submachine(builder='decoder', application=dict(input='latent', output='reconstruction'))

	criterion = submachine(builder='comparison', application=dict(input='reconstruction', target='observation', output='loss'))


	@submachine(builder='comparison', application=dict(input='reconstruction', target='observation', output='loss'))
	def criterion(self, spec):
		'''
		variant of the standard custom hparam initialization, given the parent_spec.sub('criterion')
		output treated as final value -> replaces validation
		'''
		builder = spec.get_builder()
		return builder.build(inplace=False) # hard-coded building of the default criterion


	def _default_submodule_intialization(self, spec):
		builder = spec.get_builder()

		sub = builder.build()

		return spec.validate(sub)



class LinearBuilder(Builder):
	din = space('input')
	dout = space('output')


	def product_signatures(self, *args, **kwargs):
		yield self._Signature('output', inputs=('input'))


	def product_base(self, *args, **kwargs):
		return nn.Linear


	def _build_kwargs(self, product, *, in_features=None, out_features=None, bias=None, **kwargs):
		kwargs = super()._build_kwargs(product, **kwargs)

		if in_features is None:
			in_features = self.din.width
		kwargs['in_features'] = in_features

		if out_features is None:
			out_features = self.dout.width
		kwargs['out_features'] = out_features

		return kwargs





















