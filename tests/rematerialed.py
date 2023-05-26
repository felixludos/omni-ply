import numpy as np
# import torch

from omniplex.data.materials import Materialed, material
from omniplex.structure import spaces, Decoder, Generator, NormalDistribution
from omniplex.features import Seeded
from omniplex.parameters import hparam, inherit_hparams

from omniplex.data.flavors import Synthetic, Sampledstream
from omniplex.data.top import Datastream, Dataset, Buffer



class ManifoldStream(Synthetic, Datastream, Seeded, Decoder, Generator):
	class Batch(Synthetic, Datastream.Batch):
		pass

	observation = material() # get

	@observation.transformation # get_key
	def decode(self, mechanism):
		raise NotImplementedError

	manifold = material('target', 'mechanism')

	@manifold.get_from_size
	def generate_mechanism(self, N):
		with self.force_rng(rng=self.rng):
			return self.mechanism_space.sample(N)

	def generate(self, N): # generates observations
		return self.decode(self.generate_mechanism(N))



class Stochastic(ManifoldStream):
	observation = material(src='observation')

	@observation.transformation # get_key
	def generate_observation_from_mechanism(self, mechanism):
		with self.force_rng(rng=self.rng):
			return self.decode_distrib(mechanism).sample()

	def decode_distrib(self, mechanism):
		return self._decode_distrib_from_mean(self.decode(mechanism))

	def _decode_distrib_from_mean(self, mean):
		raise NotImplementedError



class Noisy(Stochastic):
	noise_std = hparam(0., space=spaces.HalfBound(min=0.))#, alias='noise-std')

	def _decode_distrib_from_mean(self, mean):
		return NormalDistribution(mean, self.noise_std * torch.ones_like(mean))



class SwissRoll(ManifoldStream):
	Ax = hparam(np.pi / 2, space=spaces.HalfBound(min=0.))
	Ay = hparam(21., space=spaces.HalfBound(min=0.))
	Az = hparam(np.pi / 2, space=spaces.HalfBound(min=0.))

	freq = hparam(0.5, space=spaces.HalfBound(min=0.))
	tmin = hparam(3., space=spaces.HalfBound(min=0.))
	tmax = hparam(9., space=spaces.HalfBound(min=0.))

	manifold = material(replaces='mechanism')

	@manifold.space
	def mechanism_space(self):
		return spaces.Joint(
			spaces.Bound(min=self.tmin, max=self.tmax),
			spaces.Bound(min=0., max=1.),
		)

	target = material(replaces='target')

	@target.space
	def target_space(self):
		return self.mechanism_space[0]

	@target.transformation
	def get_target_from_mechanism(self, mechanism):
		return mechanism.narrow(-1,0,1)

	observation = material(replaces='observation')

	@observation.space
	def observation_space(self):
		return spaces.Joint(
			spaces.Bound(min=-self.Ax * self.tmax, max=self.Ax * self.tmax),
			spaces.Bound(min=0., max=self.Ay),
			spaces.Bound(min=-self.Az * self.tmax, max=self.Az * self.tmax),
		)

	def get_observation_from_mechanism(self, mechanism):
		theta = mechanism.narrow(-1,0,1)
		height = mechanism.narrow(-1,1,1)

		pts = torch.cat([
			self.Ax * theta * theta.mul(self.freq*np.pi).cos(),
			self.Ay * height,
			self.Az * theta * theta.mul(self.freq*np.pi).sin(),
		], -1)
		return pts



class RandomMapping(Dataset):
	N = hparam(1000, space=spaces.HalfBound(min=1))
	D = hparam(10, space=spaces.HalfBound(min=1))
	M = hparam(2, space=spaces.HalfBound(min=1))

	@material(space=spaces.Unbound())
	def X(self):
		return torch.randn(self.N, self.D)
	@X.space
	def X_space(self):
		return spaces.Unbound(self.D)

	class Y_Buffer(Buffer):
		pass

	@material
	def Y(self):
		return self.Y_Buffer()
	@Y.space
	def Y_space(self):
		return spaces.Unbound(self.M)



class MNIST(Dataset):
	class ImageBuffer(Material):
		def get_from(self, source, key):
			imgs = super().get_from(source, key)
			return imgs if self.space.as_bytes else imgs.float() / 255.

	@material
	def observation(self):
		return self.ImageBuffer()
	@observation.space
	def observation_space(self):
		size = (32, 32) if self.resize else (28, 28)
		return spaces.Pixels(1, *size, as_bytes=self._as_bytes)
	@observation.get_from_indices
	def get_observation(self, indices):
		return self.observation.data[indices]



class RandomCrop(MNIST):
	observation = material(replaces='observation')

	@observation.get_from_indices
	def get_observation(self, indices):
		return super().get_observation(indices).random_crop(self.size)



class RandomCrop2(MNIST):
	original = material.replacement('observation')

	observation = material(replaces='observation')
	
	@material.get_from_indices('original')
	def get_observation(self, indices):
		return super().get_observation(indices)
		
	
	@machine('observation')
	def get_cropped_observation(self, original):
		return original.random_crop(self.size)




class Classifier:
	@machine('loss')
	def compute_loss(self, observation, target):
		return self.criterion(self(observation), target)



class Autoencoder:
	encoder = submodule(builder='encoder')
	decoder = submodule(builder='decoder')

	@machine('latent')
	def encode(self, observation):
		return self.encoder(observation)
	@encode.space
	def latent_space(self):
		return self.encoder.output_space

	@machine('reconstruction')
	def decode(self, latent):
		return self.decoder(latent)
	@decode.space('reconstruction')
	def reconstruction_space(self):
		return self.decoder.output_space

	@machine('loss')
	def compute_loss(self, observation, reconstruction):
		return self.criterion(reconstruction, observation)



class VAE:
	@machine('posterior')
	def encode(self, observation):
		raise NotImplementedError

	@machine('latent')
	def sample_posterior(self, posterior):
		raise NotImplementedError

	@machine('reg-loss')
	def compute_kl_loss(self, posterior):
		raise NotImplementedError

	@machine('rec-loss')
	def compute_reconstruction_loss(self, observation, reconstruction):
		return self.criterion(reconstruction, observation)

	@machine('loss')
	def compute_vae_loss(self, rec_loss, reg_loss):
		return rec_loss + reg_loss



class VAE2:
	@machine('posterior')
	def encode(self, observation):
		raise NotImplementedError

	@machine('latent')
	def sample_posterior(self, posterior):
		raise NotImplementedError

	@machine('loss', 'rec-loss', 'reg-loss')
	def compute_vae_loss(self, observation, reconstruction, posterior):
		rec_loss = self.criterion(reconstruction, observation)
		reg_loss = self.compute_kl_loss(posterior)
		return rec_loss + reg_loss, rec_loss, reg_loss


class VAE3:
	@machine.from_batch('posterior')
	def encode(self, batch):
		return self.encoder(batch['observation'])

	@machine.from_context('latent')
	def sample_posterior(self, ctx):
		size = ctx.batch.size
		posterior = ctx['posterior']
		return posterior.sample()

	@machine('loss', 'rec-loss', 'reg-loss')
	def compute_vae_loss(self, observation, reconstruction, posterior):
		rec_loss = self.criterion(reconstruction, observation)
		reg_loss = self.compute_kl_loss(posterior)
		return rec_loss + reg_loss, rec_loss, reg_loss




class SimpleTrainer:
	model = submodule(None, builder='model')

	Depot = None

	def __init__(self, model=None, **kwargs):
		super().__init__(**kwargs)
		self.model = model


	def create_depot(self, *sources, **kwargs):
		if self.Depot is None:
			return self.model.Depot(*sources, self, **kwargs)
		return self.Depot(*sources, self, **kwargs)


	def step(self, info):
		loss = info['loss']

		if self.debug_mode and (info.batch.size, ) != loss.shape:
			raise ValueError(f'Loss shape does not match batch size: {loss.shape} != {info.batch.size}')

		if self.training:
			self.optimizer.zero_grad()
			loss.backward()
			self.optimizer.step()


class GAN_Trainer:
	def discriminator_step(self, info):
		disc_loss = info['disc-loss']

		self.discriminator_optim.zero_grad()
		disc_loss.backward()
		self.discriminator_optim.step()


	def generator_step(self, info):
		gen_loss = info['gen-loss']

		self.generator_optim.zero_grad()
		gen_loss.backward()
		self.generator_optim.step()


	def step(self, info):
		self.discriminator_step(info)
		self.generator_step(info)



class GAN(Model, gizmo_aliases={'real': 'observation'}):
	# aliases usually in __init__, and mainly for gets (optionally sets)
	generator = submodule(builder='generator')
	discriminator = submodule(builder='discriminator')


	Depot = None
	def create_depot(self, batch=None, **info):
		return self.Depot(self, batch, **info)

	# @machine({'samples', 'fake'}) # not the same -> makes samples and fake identitcal!
	@material.get_from_size('fake')
	@material.get_from_size('samples')
	@machine.optional('samples')
	@machine.optional('fake')
	def generate(self, batch_size):
		return self.generator(batch_size)

	# samples = material('samples', 'fake')
	# @samples.get_from_size
	# def generate(self, N):
	# 	return self.generator(N)


	@machine('disc-loss')
	def compute_discriminator_loss(self, real, fake):
		real_score = self.discriminator(real)
		fake_score = self.discriminator(fake)
		return self.criterion(real_score, self.real_target) + self.criterion(fake_score, self.fake_target)


	@machine('gen-loss')
	def compute_generator_loss(self, samples):
		gen_score = self.discriminator(samples)
		return self.criterion(gen_score, self.real_target)


	def _discriminator_step(self, info):
		disc_loss = info['disc-loss']

		if self.training:
			self.discriminator_optim.zero_grad()
			disc_loss.backward()
			self.discriminator_optim.step()


	def _generator_step(self, info):
		gen_loss = info['gen-loss']

		if self.training:
			self.generator_optim.zero_grad()
			gen_loss.backward()
			self.generator_optim.step()


	@trainer.checkpoint
	def _extra_checkpoint_info(self, info):
		info['counter'] = self.counter


	@trainer.prepare
	def init_optimizers(self):
		self.generator_optim = Adam(self.generator.parameters())
		self.discriminator_optim = Adam(self.discriminator.parameters())


	@trainer.step
	def step(self, info):
		self._discriminator_step(info)
		self._generator_step(info)


	@trainer.eval_step
	def eval_step(self, info):
		gen_loss = info['gen-loss']
		disc_loss = info['disc-loss']


	@trainer.log
	def log(self, info):
		self.logger.log_scalar('gen-loss', info['gen-loss'])
		self.logger.log_scalar('disc-loss', info['disc-loss'])


	@trainer.log_viz
	def visualize(self, info):
		self.logger.log_image('generated', info['generated'])



class Multistep(GAN):
	n_disc_steps = hparam(4)

	def _discriminator_step(self, info):
		for i in range(self.n_disc_steps):
			if i > 0:
				info.clear_cache()
				info.new_batch() # info.transition()
			super()._discriminator_step(info)




class ClassificationAnnex: # (logits, target) -> {loss, correct, accuracy, confidences, confidence}
	@machine.optional('prediction')
	def compute_prediction(self, logits):
		return logits.argmax(-1)

	@machine('correct')
	@indicator.optional('loss')
	def compute_loss(self, logits, target):
		return F.cross_entropy(logits, target)

	@machine('correct')
	@indicator.mean('accuracy')
	def compute_correct(self, prediction, target):
		return (prediction == target).float()

	@machine('confidences')
	@indicator.samples('confidence') # for multiple statistics
	def compute_confidences(self, logits):
		return logits.softmax(dim=1).max(dim=1).values



class Depot(Container):
	@machine.from_batch('batch-size')
	def _get_batch_size(self, batch):
		return batch.size














# RE:RE:Materialed




class ManifoldStream(Synthetic, Datastream, Seeded, Decoder, Generator):
	class Batch(Synthetic, Datastream.Batch):
		pass

	@material.get_from_size(('mechanism', 'target'))
	def generate_mechanism(self, N):
		with self.force_rng(rng=self.rng):
			return self.mechanism_space.sample(N)

	# @material.get_from_size('observation')
	def generate(self, N): # generates observations
		return self.decode(self.generate_mechanism(N))

	@machine('observation')
	def decode(self, mechanism):
		raise NotImplementedError



class Stochastic(ManifoldStream):
	@machine('observation')
	def generate_observation_from_mechanism(self, mechanism):
		with self.force_rng(rng=self.rng):
			return self.decode_distrib(mechanism).sample()

	def decode_distrib(self, mechanism):
		return self._decode_distrib_from_mean(self.decode(mechanism))

	def _decode_distrib_from_mean(self, mean):
		raise NotImplementedError



class Noisy(Stochastic):
	noise_std = hparam(0., space=spaces.HalfBound(min=0.))#, alias='noise-std')

	def _decode_distrib_from_mean(self, mean):
		return NormalDistribution(mean, self.noise_std * torch.ones_like(mean))



class SwissRoll(ManifoldStream):
	Ax = hparam(np.pi / 2, space=spaces.HalfBound(min=0.))
	Ay = hparam(21., space=spaces.HalfBound(min=0.))
	Az = hparam(np.pi / 2, space=spaces.HalfBound(min=0.))

	freq = hparam(0.5, space=spaces.HalfBound(min=0.))
	tmin = hparam(3., space=spaces.HalfBound(min=0.))
	tmax = hparam(9., space=spaces.HalfBound(min=0.))

	@material.space('mechanism')
	def mechanism_space(self):
		return spaces.Joint(
			spaces.Bound(min=self.tmin, max=self.tmax),
			spaces.Bound(min=0., max=1.),
		)

	@machine('target')
	def get_target_from_mechanism(self, mechanism):
		return mechanism.narrow(-1,0,1)

	@machine.space('target')
	def target_space(self):
		return self.mechanism_space[0]

	@material.space('observation')
	def observation_space(self):
		return spaces.Joint(
			spaces.Bound(min=-self.Ax * self.tmax, max=self.Ax * self.tmax),
			spaces.Bound(min=0., max=self.Ay),
			spaces.Bound(min=-self.Az * self.tmax, max=self.Az * self.tmax),
		)

	def decode(self, mechanism):
		theta = mechanism.narrow(-1,0,1)
		height = mechanism.narrow(-1,1,1)

		pts = torch.cat([
			self.Ax * theta * theta.mul(self.freq*np.pi).cos(),
			self.Ay * height,
			self.Az * theta * theta.mul(self.freq*np.pi).sin(),
		], -1)
		return pts



class RandomMapping(Dataset):
	N = hparam(1000, space=spaces.HalfBound(min=1))
	D = hparam(10, space=spaces.HalfBound(min=1))
	M = hparam(2, space=spaces.HalfBound(min=1))


	@material
	def X(self):
		return torch.randn(self.N, self.D) # if a tensor is returned, the default buffer is used to wrap it
	@X.space
	def X_space(self):
		return spaces.Unbound(self.D)

	class Y_Buffer(Buffer): # is a material subclass
		pass

	@material('Y')
	def Y(self):
		return self.Y_Buffer()
	@Y.space
	def Y_space(self):
		return spaces.Unbound(self.M)


class ToyDataset(Dataset):

	target = material() # defaults to a tensor buffer


	# @observation.get_from_indices
	# def get_observation(self, indices):
	# 	return self.observation.data[indices]

	class ImageBuffer(Dataset.Buffer):
		def get_from(self, source, key):
			imgs = super().get_from(source, key)
			return imgs if self.space.as_bytes else imgs.float() / 255.

	@material
	def observation(self):
		return self.ImageBuffer()
	@observation.space
	def observation_space(self):
		size = (32, 32) if self.resize else (28, 28)
		return spaces.Pixels(1, *size, as_bytes=self._as_bytes)

	@target.space
	def target_space(self):
		return spaces.Categorical(10)

	def _prepare(self): # no need for material specific prepare()s
		self.observation.data = self._load_observation()
		self.target.data = self._load_target()



# class MNIST(ToyDataset):


class Observation(expected=['observation']):
	pass


class Transform(Observation, replacements={'observation': 'original'}):
	@machine('observation')
	def transform_observation(self, original):
		return original



class RandomCrop(Transform):
	size = hparam(4, suggested=[0, 1, 2, 4, 5, 8, 10])

	def transform_observation(self, original):
		obs = super().transform_observation(original)
		crop = self._do_random_crop(obs, self.size)
		return crop


class Extracted_Transform(Transform):
	extractor = submodule(builder='extractor')

	def transform_observation(self, original):
		return self.extractor(super().transform_observation(original))

	@machine.prepare('observation')
	def _prepare_extractor(self):
		for param in self.extractor.parameters():
			param.requires_grad = False

	@machine.space('observation')
	def observation_space(self):
		return self.extractor.output_space



class Extracted(Observation, replacements={'observation': 'original'}):
	extractor = submodule(builder='extractor', signature=['original'], gizmo='observation')

	@machine.prepare('observation')
	def _prepare_extractor(self): # replaces default (extractor.prepare)
		self.extractor.prepare()
		for param in self.extractor.parameters():
			param.requires_grad = False

	@machine.space('observation')
	def observation_space(self): # replaces default (extractor.dout)
		return self.extractor.output_space


