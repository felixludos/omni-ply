
import sys, os
import yaml

import torch
from torch import nn
from torch.nn import functional as F

from omnibelt import unspecified_argument, agnostic
import omnifig as fig

from functools import lru_cache

import omnidata as od
from omnidata import toy
from omnidata import Builder, Buildable, HierarchyBuilder, RegisteredProduct, MatchingBuilder
from omnidata import hparam, inherit_hparams, submodule, submachine, spaces
from omnidata import Guru, Context, material, space, indicator, machine, Parameterized
from omnidata.data import toy

from omnidata import Spec, Builder, Buildable


class Basic_Autoencoder(Parameterized):
	encoder = submodule(builder='encoder')
	decoder = submodule(builder='decoder')

	criterion = submodule(builder='criterion')


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
	print('\n'.join(map(str, BetaVAE.signatures())))

	# print()
	# print('\n'.join(map(str, SimCLR.signatures())))




class AE(Parameterized):
	encoder = submachine(builder='encoder', application=dict(input='observation', output='latent'))
	decoder = submachine(builder='decoder', application=dict(input='latent', output='reconstruction'))

	criterion = submachine(builder='criterion', application=dict(input1='reconstruction', input2='observation',
	                                                             output='loss'))

	# latent_dim = hparam(required=True)
	#
	#
	# @space('latent')
	# def latent_space(self):
	# 	return spaces.Unbound(self.latent_dim)



@inherit_hparams('decoder', 'criterion')
class VAE(AE, replace={'loss': 'rec_loss'}):
	encoder = submachine(builder='encoder', application=dict(input='observation', output='posterior'))

	@space('posterior')
	def posterior_space(self):
		return spaces.Unbound(2 * self.latent_space.width)


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



class Conditional_VAE(VAE, replace={'content': 'latent'}):
	@machine('latent')
	def get_latent_codes(self, content, style):
		return torch.cat([content, style], dim=1)



@inherit_hparams('encoder', 'decoder', 'criterion')
class BetaVAE(VAE):
	beta = hparam(1.0)


	def compute_loss(self, rec_loss, reg_loss):
		return rec_loss + self.beta * reg_loss



class SimCLR(Parameterized):
	encoder = submachine(builder='encoder', application=dict(input='observation', output='latent'))
	augmentation = submodule(builder='augmentation') # augmentation must be stochastic

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



class GAN(Parameterized, replace={'real': 'observation'}):
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




class Extracted(Parameterized, replace={'observation': 'original'}):
	extractor = submachine(builder='encoder', application=dict(input='original', output='observation'))














