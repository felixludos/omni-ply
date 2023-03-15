
import sys, os
import yaml

import torch
from torch import nn

from omnibelt import unspecified_argument, agnostic
import omnifig as fig

import omnidata as od
from omnidata import toy
from omnidata import Builder, Buildable, HierarchyBuilder, RegisteredProduct, MatchingBuilder
from omnidata import hparam, inherit_hparams, submodule, spaces
from omnidata import Guru, Context, Industrial, material, space, indicator, machine
from omnidata.data import toy



class Data(HierarchyBuilder):
	pass



class Toy(Data, branch='toy', default_ident='swiss-roll', products={
	'swiss-roll': toy.SwissRollDataset,
	'helix': toy.HelixDataset,
	}):
	pass



class Manifolds(Data, branch='manifold', default_ident='swiss-roll', products={
	'swiss-roll': toy.SwissRoll,
	'helix': toy.Helix,
	}):
	pass



def test_branches():
	data = Data()

	print()
	for name, product in data.product_hierarchy():
		print(name, product)

	cls = data.product('toy/swiss-roll')
	assert cls is toy.SwissRollDataset

	cls = data.product('manifold/swiss-roll')
	assert cls is toy.SwissRoll



def test_building():
	builder = Data()

	dataset = builder.build('toy/swiss-roll', n_samples=1000)
	assert isinstance(dataset, toy.SwissRollDataset)

	stream = builder.build('manifold/swiss-roll')
	assert isinstance(stream, toy.SwissRoll)




from omnidata import Spec, Builder, Buildable



class LinearBuilder(Builder):
	din = space('input')
	dout = space('output')


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



def test_spec():
	dataset = Data().build('toy/swiss-roll', n_samples=100)

	spec = Spec().include(dataset)
	print(spec)

	builder = LinearBuilder(blueprint=spec, relabeling={'input': 'observation', 'output': 'target'})

	model = builder.build()

	assert isinstance(model, nn.Linear)
	assert model.din.width == 3
	assert model.dout.width == 1



# class PytorchModel:
# 	pass



class Linear(Buildable, nn.Linear):
	din = space('input')
	dout = space('output')
	
	
	class _Builder(SimpleBuilder):
		def _build_kwargs(self, product, *, in_features=None, out_features=None, bias=None, **kwargs):
			kwargs = super()._build_kwargs(product, **kwargs)
			
			if in_features is None:
				in_features = self.din.width
			kwargs['in_features'] = in_features
			
			if out_features is None:
				out_features = self.dout.width
			kwargs['out_features'] = out_features
			
			return kwargs



# class Autoencoder:
# 	encoder = submodule(builder='encoder')
# 	decoder = submodule(builder='decoder')
#
# 	@machine('latent')
# 	def encode(self, observation):
# 		return self.encoder(observation)
# 	@encode.space
# 	def latent_space(self):
# 		return self.encoder.output_space
#
# 	@machine('reconstruction')
# 	def decode(self, latent):
# 		return self.decoder(latent)
# 	@decode.space
# 	def reconstruction_space(self):
# 		return self.decoder.output_space
#
# 	@machine('loss')
# 	def compute_loss(self, observation, reconstruction):
# 		return self.criterion(reconstruction, observation)

















