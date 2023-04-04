
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




def example_building():

	dataset = toy.SwissRollDataset(n_samples=1000)

	spec = Spec()

	# builders are proxies for structured objects (so they may arbitrarily modify their products)

	spec['ident'] = 'linear' # set settings/hparams
	spec['nonlin.inplace'] = True # deep set

	spec.include(dataset) # include in context

	builder = LinearBuilder()

	linear = builder.build_with_spec(spec) # implicit conditioning

	linear = builder.build('linear') # auto conditioning

	linear = LinearBuilder(ident='linear').build() # init conditioning

	linear = builder(ident='linear').build() # manual conditioning (updates existing params)


# builders are nodes in the spec tree, when instantiating structured objects, the build is implicit



class DenseLayer(SimpleFunction, nn.Module, AbstractBlock, output='output', inputs=('input',)):
	linear = submodule(builder='linear')

	norm = submodule(None, builder='norm')
	nonlin = submodule('elu', builder='nonlin')
	dropout = submodule(None, builder='dropout')


	din = space('input')
	dout = space('output')


	def block_layers(self):
		if self.linear is not None:
			yield self.linear
		if self.norm is not None:
			yield self.norm
		if self.nonlin is not None:
			yield self.nonlin
		if self.dropout is not None:
			yield self.dropout


	def forward(self, x):
		x = self.linear(x)
		if self.norm is not None:
			x = self.norm(x)
		if self.nonlin is not None:
			x = self.nonlin(x)
		if self.dropout is not None:
			x = self.dropout(x)
		return x


class MLP(SimpleFunction, nn.Module, AbstractBlock, output='output', inputs=('input',)):
	hidden = hparam(())

	nonlin = subcontractor('elu', builder='nonlin')
	dropout = subcontractor(None, builder='dropout')

	out_nonlin = subcontractor(None, builder='nonlin')

	din = space('input')
	dout = space('output')






class DeepBuilder(FeedforwardBuilder):
	hidden_widths = hparam(()) # sequence of spaces

	hidden_layer = subplier('layer')
	out_layer = subplier('layer')

	# din = space('input')
	# dout = space('output')


	def build(self, spec):
		hidden_widths = self.hidden_widths

		if not len(hidden_widths):
			return self.out_layer.build(spec.sub('out_layer'))

		# assert self.din is not None and self.dout is not None, f'input and output dimensions must be specified'

		if self.din is None:
			assert self.dout is not None, f'input or output dimensions must be specified'
			...

		elif self.dout is None:

			...

			pass
		else:
			prev = self.din
			hidden_layers = []

			for width in hidden_widths:
				hidden_spec = spec.sub('hidden_layer').apply(output=width, input=prev)
				hidden_layers.append(self.hidden_layer.build(hidden_spec))
				prev = hidden_spec.space_of('output')

			out_layer = self.out_layer.build(spec.sub('out_layer').apply(output=self.dout, input=prev))

		return {'hidden': hidden_layers, 'out': out_layer}






class MLPBuilder(FeedforwardBuilder):
	hidden = hparam(())

	nonlin = subcontractor('elu', builder='nonlin')
	dropout = subcontractor(None, builder='dropout')

	out_nonlin = subcontractor(None, builder='nonlin')

	din = space('input')
	dout = space('output')




class DeepBuilder(FeedforwardBuilder):
	hidden = hparam(())  # sequence of spaces

	hidden_layer = submodule(builder='layer')
	out_layer = submodule(builder='layer')

	# din = space('input')
	# dout = space('output')

	def build(self, spec):
		hidden_widths = self.hidden_widths

		if not len(hidden_widths):
			return self.out_layer.build(spec.sub('out_layer'))

		# assert self.din is not None and self.dout is not None, f'input and output dimensions must be specified'

		if self.din is None:
			assert self.dout is not None, f'input or output dimensions must be specified'
			...

		elif self.dout is None:

			...

			pass
		else:
			prev = self.din
			hidden_layers = []

			for width in hidden_widths:
				hidden_spec = spec.sub('hidden_layer').apply(output=width, input=prev)
				hidden_layers.append(self.hidden_layer.build(hidden_spec))
				prev = hidden_spec.space_of('output')

			out_layer = self.out_layer.build(spec.sub('out_layer').apply(output=self.dout, input=prev))


		self.hidden = hidden_layers
		self.out_layer = out_layer

		return {'hidden': hidden_layers, 'out': out_layer}


from typing import Sequence


class Feedforward(Structured, SimpleFunction, nn.Sequential, output='output', inputs=('input',)):
	layers = submodule(required=True, help='layer builder, can be a list of builders or spaces')


	def _build(self, spec, layers=None): # can modify spec to fill in context of created product
		din, dout = spec.space_of('input'), spec.space_of('output') # spec contains space info (top-down)

		layers = self.layers
		assert isinstance(layers, Sequence) and len(layers), f'no (or invalid) layers given, got {layers}'

		products = []

		for layer in layers:
			if isinstance(layer, Builder):
				layer_spec = spec.sub('layers').apply(input=din)
				products.append(layer.build_from_spec(spec.sub('layer')))
			else:
				layer_spec = layer.my_blueprint
			din = layer_spec.space_of('output')

		self.layers = products
		for i, product in enumerate(products):
			self.add_module(f'{i}', product)

		return self


		# layer_builder = spec.builder_of('layers') # builder is inferred from class submodule (but can be overridden)
		#
		# layer_widths = self.layers
		#
		# layers = []
		#
		# for width in self.layers:
		# 	hidden_spec = spec.sub('hidden_layer').apply(output=width, input=prev)
		# 	hidden_layers.append(self.hidden_layer.build(hidden_spec))
		# 	prev = hidden_spec.space_of('output')
		#
		# out_layer = self.out_layer.build(spec.sub('out_layer').apply(output=self.dout, input=prev))
		#
		#
		# self.hidden = hidden_layers
		# self.out_layer = out_layer
		#
		#
		# hidden_widths = self.hidden_widths
		#
		# if not len(hidden_widths):
		# 	return self.out_layer.build(spec.sub('out_layer'))
		#
		# # assert self.din is not None and self.dout is not None, f'input and output dimensions must be specified'
		#
		# if self.din is None:
		# 	assert self.dout is not None, f'input or output dimensions must be specified'
		# 	...
		#
		# elif self.dout is None:
		#
		# 	...
		#
		# 	pass
		# else:
		# 	prev = self.din
		# 	hidden_layers = []
		#
		# 	for width in hidden_widths:
		# 		hidden_spec = spec.sub('hidden_layer').apply(output=width, input=prev)
		# 		hidden_layers.append(self.hidden_layer.build(hidden_spec))
		# 		prev = hidden_spec.space_of('output')
		#
		# 	out_layer = self.out_layer.build(spec.sub('out_layer').apply(output=self.dout, input=prev))
		#
		#
		# self.hidden = hidden_layers
		# self.out_layer = out_layer
		#
		# return {'hidden': hidden_layers, 'out': out_layer}



	pass


class FeedforwardBuilder(FeedforwardBuilder):
	layers = submodule(required=True, builder='layer', help='layer builder, can be a list of builders or spaces')

	def _build(self, spec):
		din, dout = spec.space_of('input'), spec.space_of('output')  # spec contains space info (top-down)

		layers = self.layers
		assert isinstance(layers, Sequence) and len(layers), f'no (or invalid) layers given, got {layers}'

		if isinstance(layers[0], Builder):

			products = []

			for layer in layers:
				layer_spec = spec.sub('layers').apply(input=din)
				products.append(layer.build(spec.sub('layer')))
				din = layer_spec.space_of('output')

			self.layers = products

		return self













