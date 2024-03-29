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

	@machine('observation')
	def decode(self, mechanism):
		raise NotImplementedError

	@material.get_from_size('mechanism')
	def generate_mechanism(self, N):
		with self.force_rng(rng=self.rng):
			return self.mechanism_space.sample(N)

	def generate(self, N): # generates observations
		return self.decode(self.generate_mechanism(N))



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

	@space('mechanism')
	def mechanism_space(self):
		return spaces.Joint(
			spaces.Bound(min=self.tmin, max=self.tmax),
			spaces.Bound(min=0., max=1.),
		)

	@space('target')
	def target_space(self):
		return self.mechanism_space[0]

	@space('observation')
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

	@machine('target')
	def get_target_from_mechanism(self, mechanism):
		return mechanism.narrow(-1,0,1)



class RandomMapping(Dataset):
	N = hparam(1000, space=spaces.HalfBound(min=1))
	D = hparam(10, space=spaces.HalfBound(min=1))
	M = hparam(2, space=spaces.HalfBound(min=1))

	@material
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



class RandomCrop(MNIST): # "api specific"
	def get_observation(self, indices):
		return super().get_observation(indices).random_crop(self.size)



class RandomCrop2(MNIST, replacing={'original': 'observation'}):
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

	criterion = submodule(builder='similarity')

	@machine('latent')
	def encode(self, observation):
		return self.encoder(observation)
	@encode.space
	def latent_space(self):
		return self.encoder.output_space

	@machine('reconstruction')
	def decode(self, latent):
		return self.decoder(latent)
	@decode.space
	def reconstruction_space(self):
		return self.decoder.output_space

	@machine('loss')
	def compute_loss(self, observation, reconstruction):
		return self.criterion(reconstruction, observation)



class Autoencoder2:
	encoder = submachine(builder='encoder', input='observation', output='latent')
	decoder = submachine(builder='decoder', input='latent', output='reconstruction')

	@machine('loss')
	def compute_loss(self, observation, reconstruction):
		return self.criterion(reconstruction, observation)



class Autoencoder3:
	encoder = submodule(builder='encoder')
	@machine('latent')
	def encode(self, observation):
		return self.encoder(observation)

	decoder = submodule(builder='decoder')
	@machine('reconstruction')
	def decode(self, latent):
		return self.decoder(latent)

	@machine('loss')
	def compute_loss(self, observation, reconstruction):
		return self.criterion(reconstruction, observation)



class SharedEncoder:
	encoder = submachine(builder='encoder')

	@machine('latent1')
	def encode1(self, observation1):
		return self.encoder(observation1)

	@machine('latent2')
	def encode2(self, observation2):
		return self.encoder(observation2)

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
	def generate(self, N):
		return self.generator(N)

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
				info.new_batch()
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



build = classmethod



class Function:
	@classmethod
	def build_for(cls, din, dout):




		pass


class CNN_Layer:
	@classmethod
	def build_with(cls, inp=None, out=None):
		assert inp is not None or out is not None





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

	class _ImageBuffer(Dataset._Buffer):
		def get_from(self, source, key):
			imgs = super().get_from(source, key)
			return imgs if self.space.as_bytes else imgs.float() / 255.

	@material
	def observation(self):
		return self._ImageBuffer()
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











def train_loop(config):

	context = config.pull('context')

	dataset = config.pull('dataset')
	context.add(dataset)

	model = config.pull('model')
	context.add(model)

	trainer = config.pull('trainer', None)
	if trainer is None:
		trainer = model.trainer(dataset)

	return trainer.fit()


def train_loop2(config):

	context = config.pull('context') # context is the trainer here!

	dataset = config.pull('dataset')
	# context.add(dataset) # automatic!

	model = config.pull('model')
	# context.add(model) # automatic!

	# do stuff with dataset and model
	return context.fit()



def train_loop3(config):

	dataset = config.pull('dataset')

	model = config.build_with('model', dataset)

	trainer = config.pull('trainer', None)

	trainer.add_model(model)
	trainer.fit(dataset)



	model = build_with(config, 'model')

	trainer.add_model(model)

	train_output = trainer.fit(dataset)

	eval_output = trainer.evaluate(dataset)

	return out

	context = config.pull('context') # context is the trainer here!

	dataset = config.pull('dataset')
	# context.add(dataset) # automatic!

	model = config.pull('model')
	# context.add(model) # automatic!

	# do stuff with dataset and model
	return context.fit()


from omniplex import Prepared
from omniplex.tools import space, machine


class SimpleFunction:

	din = space('input')
	dout = space('output')

	@machine('output')
	def forward(self, input):
		raise NotImplementedError



class MissingSpace(TypeError):
	pass


class Linear(Prepared):
	@space('input')
	def din(self):
		raise MissingSpace
	@space('output')
	def dout(self):
		raise MissingSpace


	def _prepare(self):
		super()._prepare()
		self.w = torch.randn(self.dout.width, self.din.width)


	@machine('output') # optional, since SimpleFunction already defines this machine
	def forward(self, input):
		return self.w @ input


# class BetterLinear:
# 	@classmethod
# 	def plan(cls, din=None, dout=None):
# 		if din is None and dout is None:
# 			raise ValueError('Either din or dout must be specified')
# 		if din is None:
# 			pass


class Width(Linear):
	width = hparam(space=spaces.Naturals(min=1))

	@space('input')
	def din(self):
		return None
	@space('output')
	def dout(self):
		return None


	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		if self.din is None:
			self.din = spaces.Unbound(self.width)
		if self.dout is None:
			self.dout = spaces.Unbound(self.width)



class Affine(Linear):
	enable_bias = hparam(True)


	def _prepare(self):
		super()._prepare()
		if self.enable_bias:
			self.b = torch.randn(self.dout.width)


	def forward(self, input):
		out = super().forward(input)
		if self.enable_bias:
			out += self.b
		return out



class Layer(Linear):
	nonlin = submodule('relu', builder='nonlin')


	def forward(self, input):
		return self.nonlin(super().forward(input))


	# @space('input')
	# def din(self, output): # means output has be to known to determine din
	# 	return spaces.Unbound(self.width)
	# @space('output')
	# def dout(self, input): # means input has be to known to determine dout
	# 	return spaces.Unbound(self.width)


	# @classmethod
	# def build(cls, din=None, dout=None, **kwargs):
	# 	if din is not None:
	# 		kwargs['din'] = din
	# 	if dout is not None:
	# 		kwargs['dout'] = dout
	# 	return cls(**kwargs)
	#
	#
	# @space.infer(din='input', dout='output')
	# def __init__(self, din=None, dout=None, **kwargs):
	# 	super().__init__(**kwargs)
	# 	assert din is not None or dout is not None
	# 	if din is not None:
	# 		self.din = din
	# 	if dout is not None:
	# 		self.dout = dout
	# 	if din is not None and dout is not None:
	# 		self.width = self.dout.width



@inherit_hparams('width', 'nonlin', 'enable_bias')
class Dropout_Layer(Layer):
	dropout = submodule(0.0, builder='dropout', space=spaces.Bound(min=0.0, max=1.0))


	def forward(self, input):
		return self.dropout(super().forward(input))



# from torch import nn



class OldMLP(nn.Sequential):
	def _build_layers(self, din, dout, hidden, nonlin, **kwargs):
		if hidden is None:
			hidden = [64, 64]
		if nonlin is None:
			nonlin = nn.ELU
		layers = []
		if din is None:
			din = spaces.Unbound()
		if dout is None:
			dout = spaces.Unbound()
		if isinstance(hidden, int):
			hidden = [hidden]
		for i, w in enumerate(hidden):
			if i == 0:
				layers.append(nn.Linear(din.width, w))
			else:
				layers.append(nn.Linear(hidden[i-1], w))
			layers.append(nonlin())
		layers.append(nn.Linear(hidden[-1], dout.width))
		return layers


	def __init__(self, *, din=None, dout=None, hidden=None, nonlin=None, **kwargs):
		layers = self._build_layers(din, dout, hidden, nonlin, **kwargs)
		super().__init__(*layers)



# class NaiveBuilder:
# 	def build_with_context(self, config, context):
# 		# dynamic capture build()
# 		pass



class BetterMLP(Prepared):
	hidden = hparam()
	nonlin = hparam('elu')
	out_nonlin = hparam(None)

	_layer_builder = 'affine'
	_nonlin_builder = 'nonlin'


	def _prepare(self):
		super()._prepare()

		layer_builder = get_builder(self._layer_builder)
		nonlin_builder = get_builder(self._nonlin_builder)

		dims = [self.din.width] + self.hidden + [self.dout.width]
		self.layers = nn.ModuleList()
		for i in range(len(dims)-1):
			self.layers.append(layer_builder.build(din=dims[i], dout=dims[i+1]))
			if i < len(dims)-2:
				self.layers.append(nonlin_builder.build(self.nonlin))
			elif self.out_nonlin is not None:
				self.layers.append(nonlin_builder.build(self.out_nonlin))


	@machine('output')
	def forward(self, input):
		out = input
		for layer in self.layers:
			out = layer(out)
		return out


	# @classmethod
	# def build():



class EvenBetterMLP:
	hidden = submodule(builder='multilayer')
	out_layer = submodule(builder='layer')

	@classmethod
	def build(cls, *, din=None, dout=None, hidden, out_layer, **kwargs):
		# hidden is an instance of the 'multilayer' builder
		# out_layer is an instance of the 'layer' builder

		if isinstance(hidden.value, int):
			hidden.value = [hidden.value]
		if isinstance(hidden.value, list):
			if din is not None:
				hidden.value = [din.width] + hidden.value
			if dout is not None:
				hidden.value = hidden.value + [dout.width]

			out_layer['din'] = hidden.value[-1]
			out_layer['dout'] = dout.width
			hidden.value = hidden.value[:-1]



	@machine('output')
	def forward(self, input):
		out = self.hidden(input)
		return self.out_layer(out)


class BestMLLP:
	hidden = submodule(builder='multilayer')
	out_layer = submodule(builder='layer')



class AE:
	encoder = submachine(builder='encoder', input='observation', output='latent')
	decoder = submachine(builder='decoder', input='latent', output='reconstruction')


	@machine('loss')
	def compute_loss(self, observation, reconstruction):
		return F.mse_loss(reconstruction, observation)



class VAE(AE):
	encoder = submachine(builder='encoder', input='observation', output='posterior')

	num_modes = hparam(1)


	@space('posterior')
	def posterior_space(self, latent):
		return spaces.Unbound(2 * latent.width * self.num_modes)


	@machine('latent')
	def sample_latent(self, posterior):
		mu, sigma = posterior.chunk(2, dim=-1)
		sigma = sigma.exp()
		eps = torch.randn_like(sigma)
		return mu + sigma * eps


	@machine('reg_loss')
	def compute_reg_loss(self, posterior):
		mu, sigma = posterior.chunk(2, dim=-1)
		return -0.5 * torch.sum(1 + sigma - mu.pow(2) - sigma.exp())


	@machine('rec_loss')
	def compute_rec_loss(self, reconstruction, observation):
		return super().compute_loss(reconstruction, observation)


	@machine('loss')
	def compute_loss(self, rec_loss, reg_loss):
		return rec_loss + reg_loss




class BestMLP:
	hidden = submachine(builder='multilayer', input='input', output='features')
	out_layer = submachine(builder='layer', input='features', output='output')



class SimpleMLP:
	hidden = submodule(builder='multilayer')
	out_layer = submodule(builder='layer')


	@machine('features')
	def extract_features(self, input):
		return self.hidden(input)


	@machine('output')
	def forward(self, features):
		return self.out_layer(features)



class MLP(nn.Sequential):
	def __init__(self, layers=(), **kwargs):
		super().__init__(*layers)



class Linear2(nn.Linear):
	din = space('input')
	dout = space('output')


	def comply(self, schema):
		# check that set spaces are compatible with schema
		# update missing (local) spaces
		self.din = schema.space_of('input')
		self.dout = schema.space_of('output')


	def _prepare(self):
		self.linear = nn.Linear(self.din.width, self.dout.width)


	@machine('output')
	def forward(self, input):
		return self.linear(input)


class WidthLInear2(Linear2):
	width = hparam()

	def _fillin_spaces(self, input=None, output=None):
		assert input is not None or output is not None
		if input is not None:
			self.din = input
		if output is not None:
			self.dout = output
		if self.din is None:
			self.din = spaces.Unbound(self.width)
		if self.dout is None:
			self.dout = spaces.Unbound(self.width)


class MultiLayer(nn.Sequential, SimpleFunction):
	layers = submodule(None)

	def __init__(self, layers=None, **kwargs):
		if layers is None:
			layers = self._build_layers()
		super().__init__(*layers, **kwargs) # <--- this is where the spaces are filled in based on context


	def _create_layer_builders(self, dims):
		raise NotImplementedError


	def _build_layers(self, *, dims=None, builders=None):
		if dims is None:
			dims = self.layers

			if dims is None:
				dims = []
			if isinstance(dims, int):
				dims = [dims]
			if isinstance(dims, list):
				if self.din is not None:
					dims = [self.din] + dims
				if self.dout is not None:
					dims = dims + [self.dout]

		if builders is None:
			builders = self._create_layer_builders(dims)

		layers = []
		for builder, din, dout in zip(builders, dims[:-1], dims[1:]):
			builder.set_space('input', din)
			builder.set_space('output', dout)
			layer = builder.build() # <--- this is where the layer is instantiated
			layers.append(layer)

		self.layers = layers

		layers = self.layers
		if len(layers):
			self.din = layers[0].din
			self.dout = layers[-1].dout



@inherit_hparams('layers')
class MLP(MultiLayer):
	out_layer = submodule(builder='layer')



class SimpleMultiLayer(MultiLayer):
	_layer_builder = 'layer'

	def _create_layer_builders(self, dims):
		return [get_builder(self._layer_builder) for d in dims[:-1]]



class MultiLayerBuilder:
	hidden = hparam()
	nonlin = hparam('elu')

	din = space('input')
	dout = space('output')

	def validate(self, obj):
		if isinstance(obj, int):
			obj = [obj]
		if isinstance(obj, list):
			return self.build(hidden=obj)
		return obj


	def product(self, *args, **kwargs):
		return MLP


	def _build_layer(self, din, dout, **kwargs):
		return nn.Linear(din, dout), nonlin()


	def build(self, *, hidden: AbstractSchema, nonlin: AbstractSchema, **kwargs):

		if isinstance(hidden, int):
			hidden = [hidden]
		if isinstance(hidden, list):
			hidden = [din.width] + hidden + [dout.width]

		layers = []
		for i in range(len(hidden)-1):
			layers.append(nn.Linear(hidden[i], hidden[i+1]))
			if i < len(hidden)-2:
				layers.append(nonlin())
		return MLP(*layers)


	@classmethod
	def plan(cls, layers, **kwargs):
		args = super().plan(**kwargs)

		for layer in layers:
			layer['din'] = cls.dout


		args['layers'] = [layer.construct() for layer in layers]
		return args



class MLP(LayerBuilder):


	pass



class AutoMLP(MLP):
	hidden = hparam(None)



	out_layer = Layer(width=1, nonlin='sigmoid')



class Trainer:
	def fit(self, dataset):

		for batch in self.iterate(dataset):
			self.step(batch)

		return self.summarize()



def train_loop4(config):

	dataset = config.pull('dataset')

	model = config.pull('model')

	trainer = config.pull('trainer').include(dataset)
	trainer.set_model(model)

	# for batch in trainer:
	# 	optimizer.step(batch)
	# return model
	return trainer.fit(dataset)


def train_loop5(config):

	dataset = config.pull('dataset')

	model = config.pull('model')

	trainer = config.pull('trainer')

	trainer.set_model(model)

	# for batch in trainer:
	# 	optimizer.step(batch)
	# return model
	return trainer.fit(dataset)



def train_loop5(config):
	dataset = config.pull('dataset')

	traindata, valdata = dataset.split(0.8)

	model = config.pull('model')

	trainer = config.pull('trainer')

	trainer.set_model(model)

	# for batch in dataset:
	# 	optimizer.step(batch)
	# return model

	trainer.fit(traindata)
	return trainer.evaluate(valdata)



class ContrastiveModel:
	extractor = submodule(builder='extractor')
	augmentation = submodule(builder='augmentation')

	margin = hparam(1.0, space=spaces.Real(0, 10))
	@submodule
	def criterion(self):
		return nn.TripletMarginLoss(margin=self.margin)


	@machine('anchor')
	def get_anchor(self, observation):
		return self.extractor(observation)


	@machine('positive')
	def get_positive(self, observation):
		return self.extractor(self.augmentation(observation))


	@material.from_size('derangement')
	def sample_derangement(self, N):
		while True:
			p = torch.randperm(N)
			if (p != torch.arange(N)).all():
				return p


	@machine('negative')
	def get_negative(self, observation, derangement):
		return self.extractor(self.augmentation(observation[derangement]))


	@machine('loss')
	def compute_loss(self, anchor, positive, negative):
		return self.criterion(anchor, positive, negative)





