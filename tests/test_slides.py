
import sys, os
from pathlib import Path
import yaml

# import torch
# from torch import nn
# from torch.nn import functional as F

from omnibelt import unspecified_argument, agnostic
import omnifig as fig

from collections import OrderedDict
from functools import lru_cache

import omniplex as od
from omniplex import toy
from omniplex import Builder, HierarchyBuilder, RegisteredProduct, MatchingBuilder, RegistryBuilder, \
	register_builder, get_builder
from omniplex import BudgetLoader
from omniplex import hparam, inherit_hparams, submodule, submachine, spaces
from omniplex import Guru, Context, material, space, indicator, machine, Structured

from omniplex import Spec, Builder, InitWall
from omniplex import toy


class Basic_Autoencoder(Structured, InitWall):#, nn.Module):
	encoder = submodule(builder='encoder')
	decoder = submodule(builder='decoder')

	criterion = submodule(builder='comparison')

	latent_dim = hparam(required=True, space=spaces.Naturals())
	
	@space('latent')
	def latent_space(self):
		return spaces.Unbound(self.latent_dim)
	
	@machine('latent')
	def encode(self, observation):
		return self.encoder(observation)
	
	@machine('reconstruction')
	def decode(self, latent):
		return self.decoder(latent)

	@machine('loss')
	def compute_loss(self, observation, reconstruction):
		return self.criterion(reconstruction, observation)



def test_signature():

	print()
	print('\n'.join(map(str, Basic_Autoencoder.signatures())))

	print()
	print('\n'.join(map(str, AE.signatures())))

	print()
	print('\n'.join(map(str, VAE.signatures())))

	print()
	print('\n'.join(map(str, GAN.signatures())))

	print()
	print('\n'.join(map(str, BetaVAE.signatures())))

	print()
	print('\n'.join(map(str, SimCLR.signatures())))



class CrossEntropyLoss():#nn.CrossEntropyLoss):
	def forward(self, input, target):
		if target.ndim > 1:
			target = target.view(-1)
		return super().forward(input, target)



# @register_builder('criterion')
# class CriterionBuilder(HierarchyBuilder, products={'cross-entropy': CrossEntropyLoss,
#                                                    'mse': nn.MSELoss}):
# 	target_space = space('target')
# 	@space('input')
# 	def input_space(self):
# 		return self.target_space
#
#
# 	def product_signatures(self, *args, **kwargs):
# 		yield self._Signature('output', inputs=('input', 'target'))



@register_builder('criterion')
class CriterionBuilder(HierarchyBuilder, products={'cross-entropy': CrossEntropyLoss,
                                                   # 'mse': nn.MSELoss
                                                   }):

	target_space = space('target')
	@space('input')
	def input_space(self):
		return self.target_space


	def product_signatures(self, *args, **kwargs):
		yield self._Signature('output', inputs=('input', 'target'))



@register_builder('comparison')
class ComparisonBuilder(CriterionBuilder, branch='comparison', default_ident='mse',
                        # products={'mse': nn.MSELoss}
                        ):
	pass



@register_builder('function')
class FunctionBuilder(Builder):
	def product_signatures(self, *args, **kwargs):
		yield self._Signature('output', inputs=('input',))


	din = space('input')
	dout = space('output')



class LinearBuilder(FunctionBuilder):

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


@register_builder('nonlin')
class Nonlin_Builder(HierarchyBuilder, branch='nonlin', default_ident='relu', products={
	# 'relu': nn.ReLU,
	# 'lrelu': nn.LeakyReLU,
	# 'prelu': nn.PReLU,
	# 'elu': nn.ELU,
	# 'sigmoid': nn.Sigmoid,
	# 'tanh': nn.Tanh,
}):
	pass


@register_builder('mlp')
class MLP_Builder(LinearBuilder):
	def product_signatures(self, *args, **kwargs):
		yield self._Signature('output', inputs=('input',))

	hidden = hparam(None)
	nonlin = hparam('elu')
	out_nonlin = hparam(None)

	def product_base(self, *args, hidden=unspecified_argument, **kwargs):
		if hidden is unspecified_argument:
			hidden = self.hidden
		return nn.Linear if hidden is None else nn.Sequential

	def _build_kwargs(self, product, **kwargs):
		kwargs = super()._build_kwargs(product, **kwargs)

		if issubclass(product, nn.Sequential):
			hidden = [kwargs.pop('in_features')] + self.hidden + [kwargs.pop('out_features')]

			nonlin_builder = get_builder('nonlin')()

			layers = []

			for i in range(len(hidden) - 1):
				layers.append(nn.Linear(hidden[i], hidden[i + 1]))
				if i < len(hidden) - 2:
					layers.append(nonlin_builder.build(self.nonlin))
				elif self.out_nonlin is not None:
					layers.append(nonlin_builder.build(self.out_nonlin))

			kwargs[None] = layers

		return kwargs


@register_builder('encoder')
class EncoderBuilder(MLP_Builder):
	pass



@register_builder('decoder')
class DecoderBuilder(MLP_Builder):
	pass



# class Classifier(Structured):
# 	net = submachine(builder='net', application=dict(input='observation', output='logits'))
# 	criterion = submachine(builder='criterion', application=dict(input='logits', target='target', output='loss'))
#
#
# 	@machine('prediction')
# 	def predict_from_logits(self, logits):
# 		return logits.argmax(dim=1)



class LVM(Structured, InitWall, nn.Module):
	latent_dim = hparam(required=True, inherit=True)


	@space('latent')
	def latent_space(self):
		return spaces.Unbound(self.latent_dim)



class AE(LVM):
	encoder = submachine(builder='encoder', application=dict(input='observation', output='latent'))
	decoder = submachine(builder='decoder', application=dict(input='latent', output='reconstruction'))

	criterion = submachine(builder='comparison', application=dict(input='reconstruction', target='observation',
	                                                             output='loss'))



@inherit_hparams('criterion', 'decoder', 'latent_dim')
class VAE(AE, replace={'loss': 'rec_loss'}):
	encoder = submachine(builder='encoder', application=dict(input='observation', output='posterior'))


	@space('posterior')
	def encoder_output_space(self):
		return spaces.Unbound(self.latent_space.width * 2)


	@machine('latent')
	def sample_posterior(self, posterior):
		mu, sigma = posterior.chunk(2, dim=-1)
		sigma = sigma.exp()
		eps = torch.randn_like(sigma)
		return mu + sigma * eps


	@machine('reg_loss')
	def compute_reg_loss(self, posterior):
		mu, sigma = posterior.chunk(2, dim=-1)
		return -0.5 * torch.sum(1 + sigma - mu.pow(2) - sigma.exp())


	@machine('loss')
	def compute_loss(self, rec_loss, reg_loss):
		return rec_loss + reg_loss



@inherit_hparams('encoder', 'decoder', 'criterion', 'latent_dim')
class Conditional_VAE(VAE, replace={'content': 'latent'}):
	@machine('latent')
	def get_latent_codes(self, content, style):
		return torch.cat([content, style], dim=1)



@inherit_hparams('encoder', 'decoder', 'criterion', 'latent_dim')
class BetaVAE(VAE):
	beta = hparam(1.0)


	def compute_loss(self, rec_loss, reg_loss):
		return rec_loss + self.beta * reg_loss



class SimCLR(LVM):
	encoder = submachine(builder='encoder', application=dict(input='observation', output='latent'))
	# augmentation = submodule(builder='augmentation') # augmentation must be stochastic

	augmentation_std = hparam(0.1)
	@submodule
	def augmentation(self):
		return lambda x: x.add(torch.randn_like(x) * self.augmentation_std)

	temperature = hparam(1.0)


	@machine('projection1')
	@machine('projection2')
	def get_projection(self, latent):
		return self.augmentation(latent)


	@machine('similarity_matrix')
	def compute_similarity_matrix(self, projection1, projection2):
		representations = torch.cat([projection1, projection2], dim=0)
		return F.cosine_similarity(representations.unsqueeze(1), representations.unsqueeze(0), dim=2)


	@machine('positives')
	def compute_positive_similarity(self, similarity_matrix):
		size = similarity_matrix.size(0) // 2
		sim_ij = torch.diag(similarity_matrix, size)
		sim_ji = torch.diag(similarity_matrix, -size)
		return torch.cat([sim_ij, sim_ji], dim=0)


	@staticmethod
	@lru_cache(maxsize=4)
	def _negatives_mask(N):
		mask = torch.eye(2*N, dtype=bool)
		corner = torch.diag(torch.ones(N, dtype=bool), N)
		mask = mask | corner | corner.T
		return ~mask


	@machine('negatives')
	def compute_negative_similarity(self, similarity_matrix):
		mask = self._negatives_mask(similarity_matrix.size(0)//2)
		return similarity_matrix[mask]


	@machine('loss')
	def compute_loss(self, positives, negatives):
		positive_logits = torch.exp(positives / self.temperature)
		negative_logits = torch.exp(negatives / self.temperature)

		scores = positive_logits.div(positive_logits.sum() + negative_logits.sum()).log()
		return -scores.sum().div(2 * len(positives))



@inherit_hparams('encoder')
class TargetedSimCLR(SimCLR):
	@machine('positives')
	def compute_positive_similarity(self, similarity_matrix, class_id):

		raise NotImplementedError


	@machine('negatives')
	def compute_negative_similarity(self, similarity_matrix, class_id):
		raise NotImplementedError




class GAN(Structured):
	generator = submodule(builder='generator')
	discriminator = submodule(builder='discriminator')

	criterion = submodule(builder='criterion')


	@material.from_size('fake') # -> for training the discriminator
	@material.from_size('samples') # -> for training the generator
	def generate(self, N):
		return self.generator(N)


	@staticmethod
	@lru_cache(maxsize=4)
	def _real_targets(N):
		return torch.ones(N, dtype=torch.float32)


	@staticmethod
	@lru_cache(maxsize=4)
	def _fake_targets(N):
		return torch.zeros(N, dtype=torch.float32)


	@machine('disc_loss')
	def compute_discriminator_loss(self, real, fake):
		real_scores = self.discriminator(real)
		fake_scores = self.discriminator(fake.detach())
		return self.criterion(real_scores, self._real_targets(len(real))) \
			+ self.criterion(fake_scores, self._fake_targets(len(fake)))


	@machine('gen_loss')
	def compute_generator_loss(self, samples):
		gen_score = self.discriminator(samples)
		return self.criterion(gen_score, self._real_targets(len(samples)))



# class ClassificationAnnex: # (logits, target) -> {loss, correct, accuracy, confidences, confidence}
# 	@machine.optional('prediction')
# 	def compute_prediction(self, logits):
# 		return logits.argmax(-1)
#
# 	@machine('correct')
# 	@indicator.optional('loss')
# 	def compute_loss(self, logits, target):
# 		return F.cross_entropy(logits, target)
#
# 	@machine('correct')
# 	@indicator.mean('accuracy')
# 	def compute_correct(self, prediction, target):
# 		return (prediction == target).float()
#
# 	@machine('confidences')
# 	@indicator.samples('confidence') # for multiple statistics
# 	def compute_confidences(self, logits):
# 		return logits.softmax(dim=1).max(dim=1).values



# class BasicExtracted(replacements={'observation': 'original'}):
# 	extractor = submodule(builder='encoder')
#
# 	def _prepare(self, *args, **kwargs):
# 		super()._prepare(*args, **kwargs)
# 		self.extractor.prepare()
# 		for param in self.extractor.parameters():
# 			param.requires_grad = False
#
# 	@machine('observation')
# 	def extract(self, original):
# 		return self.extractor(original)
# 	@extract.space
#
# 	@machine.space('observation')
# 	def observation_space(self): # replaces default (extractor.dout)
# 		return self.extractor.output_space



_PRODUCTS_PATH = Path(__file__).parent / 'products'



from omniplex.util.viz import signature_graph



def test_graph():
	g = signature_graph(AE)
	g.render(_PRODUCTS_PATH / "AE", format="png")

	g = signature_graph(GAN)
	g.render(_PRODUCTS_PATH / "GAN", format="png")

	g = signature_graph(VAE)
	g.render(_PRODUCTS_PATH / "VAE", format="png")

	g = signature_graph(Basic_Autoencoder)
	g.render(_PRODUCTS_PATH / "Basic_Autoencoder", format="png")


	g = signature_graph(SimCLR)
	g.render(_PRODUCTS_PATH / "SimCLR", format="png")


	g = signature_graph(TargetedSimCLR)
	g.render(_PRODUCTS_PATH / "TargetSimCLR", format="png")


	g = signature_graph(toy.SwissRoll)
	g.render(_PRODUCTS_PATH / "SwissRoll", format="png")


	g = signature_graph(toy.SwissRollDataset)
	g.render(_PRODUCTS_PATH / "SwissRollDataset", format="png")


	g = signature_graph(toy.Helix)
	g.render(_PRODUCTS_PATH / "Helix", format="png")



def test_init():
	dataset = toy.SwissRoll()

	spec = Spec().include(dataset)
	print(spec)

	model = VAE(latent_dim=2, blueprint=spec)

	print(model)

	print()

	print('\n'.join(map(str, model.signatures())))
	print()

	g = signature_graph(model)
	g.render(_PRODUCTS_PATH / "VAE_instance", format="png")

	batch = dataset.batch(5).include(model)

	print(batch)

	print(batch['loss'])

	print(batch)

	print()

	print('\n'.join(map(str, batch.signatures())))
	print()

	g = signature_graph(batch)
	g.render(_PRODUCTS_PATH / "batch_instance", format="png")



def test_init2():
	dataset = toy.Helix(n_helix=4)

	spec = Spec().include(dataset)
	print(spec)

	model = TargetedSimCLR(latent_dim=2, application=dict(class_id='target'), blueprint=spec)

	print(model)

	print()

	print('\n'.join(map(str, model.signatures())))
	print()

	g = signature_graph(model)
	g.render(_PRODUCTS_PATH / "SimCLR_instance", format="png")

	batch = dataset.batch(5).include(model)

	print(batch)

	g = signature_graph(batch)
	g.render(_PRODUCTS_PATH / "simclr_batch_instance", format="png")


	# print(batch['similarity_matrix'])
	# print(batch)

	print()

	print('\n'.join(map(str, batch.signatures())))
	print()



class SimpleFunction(Structured, ):#nn.Module):
	@machine('output')
	def compute(self, input):
		return self(input)



class ClassifierAnnex(Structured): # (logits, target) -> {loss, correct, accuracy, confidences, confidence}
	# net = submachine(builder='function', application=dict(input='observation', output='logit'))
	criterion = submachine('cross-entropy', builder='criterion', application=dict(input='logit', output='loss'))


	@machine.optional('prediction')
	def compute_prediction(self, logit):
		return logit.argmax(-1)


	@machine('correct')
	# @indicator.mean('accuracy')
	def compute_correct(self, prediction, target):
		return prediction == target


	@machine('confidences')
	# @indicator.samples('confidence') # for multiple statistics
	def compute_confidences(self, logit):
		return logit.softmax(dim=1).max(dim=1).values



class Manifolds(HierarchyBuilder, branch='manifold', default_ident='swiss-roll', products={
	'swiss-roll': toy.SwissRoll,
	'helix': toy.Helix,
	}):
	pass


def test_classifier():
	spec = Spec()

	dataset = Manifolds().modded(toy.Noisy).build('helix', n_helix=4, blueprint=spec)
	spec.include(dataset)

	signature_graph(dataset).render(_PRODUCTS_PATH / "cls_data_instance", format="png")


	annex = ClassifierAnnex(blueprint=spec)
	spec.include(annex)

	signature_graph(annex).render(_PRODUCTS_PATH / "cls_annex_instance", format="png")

	builder = MLP_Builder(hidden=[64,64], nonlin='relu',
	                      application=dict(input='observation', output='logit'), blueprint=spec)
	model = builder.modded(SimpleFunction).build()


	signature_graph(model).render(_PRODUCTS_PATH / "cls_model_instance", format="png")

	loader = dataset.iterate(batch_size=10)
	loader = loader.include(annex, model)

	batch = next(loader)

	signature_graph(batch).render(_PRODUCTS_PATH / "cls_batch_instance", format="png")

	print()

	print(batch)

	print(batch['loss'])

	print(batch)



class Extracted(Structured, replace={'observation': 'original'}):
	extractor = submachine(builder='encoder', application=dict(input='original', output='observation'))



# @inherit_hparams('extractor')
# class SimpleExtracted(Extracted):
	obs_dim = hparam(required=True)


	@space('observation')
	def observation_space(self):
		return spaces.Unbound(self.obs_dim)





# def test_extracted_classifier():
# 	spec = Spec()
#
# 	dataset = Manifolds().modded(Extracted, toy.Noisy).build('helix', obs_dim=12, n_helix=4, blueprint=spec)
#
# 	print(dataset)

	# spec.include(dataset)

	# signature_graph(dataset).render(_PRODUCTS_PATH / "noisy_data_instance", format="png")


	# spec = Spec()
	#
	# dataset = toy.Helix(n_helix=4, blueprint=spec)
	# spec.include(dataset)
	#
	# signature_graph(dataset).render(_PRODUCTS_PATH / "cls_data_instance", format="png")
	#
	# annex = ClassifierAnnex(blueprint=spec)
	# spec.include(annex)
	#
	# signature_graph(annex).render(_PRODUCTS_PATH / "cls_annex_instance", format="png")
	#
	# builder = MLP_Builder(hidden=[64, 64], nonlin='relu',
	#                       application=dict(input='observation', output='logit'), blueprint=spec)
	# model = builder.modded(SimpleFunction).build()
	#
	# signature_graph(model).render(_PRODUCTS_PATH / "cls_model_instance", format="png")
	#
	# loader = dataset.iterate(batch_size=10)
	# loader = loader.include(annex, model)
	#
	# batch = next(loader)
	#
	# signature_graph(batch).render(_PRODUCTS_PATH / "cls_batch_instance", format="png")
	#
	# print(batch)
	#
	# print(batch['loss'])
	#
	# print(batch)







# class DeepFunction(SimpleFunction):
# 	hidden = hparam()
#
# 	@space('features')
# 	def features_space(self):
# 		return spaces.Unbound(self.hidden[-1])
#
# 	feature_extractor = submachine(builder='mlp', application=dict(input='input', output='features'))
# 	out_layer = submachine(builder='linear', application=dict(input='features', output='output'))
#
#
#
# def test_classifier2():
# 	spec = Spec()
#
# 	dataset = toy.Helix(n_helix=4, blueprint=spec)
# 	spec.include(dataset)
#
# 	annex = ClassifierAnnex(blueprint=spec)
#
# 	spec.include(annex)
#
# 	# model = Classifier(blueprint=spec)
#
#
# 	model = DeepFunction(blueprint=spec)
#
# 	builder = MLP_Builder(hidden=[64,64], nonlin='relu',
# 	                      application=dict(input='observation', output='logit'), blueprint=spec)
# 	model = builder.modded(SimpleFunction).build()
#
#
# 	loader = dataset.iterate(batch_size=10).include(model)
#
# 	batch = next(loader)
#
# 	print(batch)



# def test_classifier():
# 	spec = Spec()
#
# 	dataset = toy.Helix(n_helix=4, blueprint=spec)
# 	# spec.include(dataset)
#
# 	# model = Classifier(blueprint=spec)
#
# 	builder = FunctionBuilder(application=dict(input='observation', output='logit'), blueprint=spec)
#
# 	builder.modded(ClassifierAnnex)
#
# 	model = builder.build()
#
# 	print(model)
#
# 	pass






