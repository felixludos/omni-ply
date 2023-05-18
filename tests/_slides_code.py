






########################################################################################################################









# from torch.utils import data


def dataset(index):
	input = ...
	target = ...
	return input, target


def model(input):
	logits = ...
	return logits


# def criterion(logits, target):
# 	loss = ...
# 	return loss


def monitor(logits, target):
	accuracy = ...
	return accuracy

def record(accuracy):
	pass










########################################################################################################################




class Loader(dataset):
	def __iter__(self):
		pass

class Optimizer(model):
	pass


def save(model):
	pass



class Model(nn.Module):
	def __init__(self, observation_space, target_space, nonlin='relu'):
		super().__init__()
		self.hidden_layers = nn.Sequential(...)
		self.output_layer = nn.Linear(10, 10)

	def forward(self, observation):
		# compute logits from observation
		features = self.hidden_layers(observation)
		logits = self.output_layer(features)
		return logits


class Dataset(data.Dataset):
	def __init__(self, **config):
		super().__init__()

	def __getitem__(self, index):
		# load observation and target from index
		observation = ...
		target = ...
		return observation, target


def criterion(logits, target):
	loss = F.cross_entropy(logits, target)
	return loss



dataset = Dataset(mode='train')
model = Model(nonlin='relu')

loader = Loader(dataset, batch_size=32)
optim = Optimizer(model, lr=0.01)

for batch in loader: # loads a batch of data
	observation, target = batch

	logit = model(observation)

	loss = criterion(logit, target)

	optim.step(loss)

	accuracy = monitor(logit, target)
	record(accuracy)

save(model)



def model(batch):
	observation = batch['observation']
	batch['logit'] = ...
	return batch


def criterion(batch):
	logit = batch['logit']
	target = batch['target']
	batch['loss'] = ...
	return batch


def monitor(batch):
	logit = batch['logit']
	target = batch['target']
	batch['accuracy'] = ...
	return batch



config = {}
dataset_config = {}
model_config = {}
loader_config = {}
optim_config = {}


class Model(nn.Module):
	def __init__(self, **config):
		super().__init__()

	def forward(self, batch):
		observation = batch['observation']
		batch['logit'] = ...
		return batch


class Dataset(data.Dataset):
	def __init__(self, **config):
		super().__init__()

	def __getitem__(self, index):
		observation = ...
		target = ...
		return observation, target


def criterion(logits, target):
	loss = ...
	return loss


dataset = Dataset(**dataset_config)
model = Model(**model_config)

loader = Loader(dataset, **loader_config)
optim = Optimizer(model, **optim_config)

for batch in loader:
	batch = model(batch)

	batch = criterion(batch)

	optim.step(batch)

	batch = monitor(batch)
	record(batch)


save(model)



class Model(nn.Module):
	def __init__(self, observation_space, target_space, nonlin='relu'):
		super().__init__()
		self.hidden_layers = nn.Sequential(...)
		self.output_layer = nn.Linear(10, 10)

	def forward(self, observation):
		# compute logits from observation
		features = self.hidden_layers(observation)
		logits = self.output_layer(features)
		return logits



class Model(Structured):
	def __init__(self, observation_space, target_space, nonlin='relu'):
		super().__init__()
		self.hidden_layers = nn.Sequential(...)
		self.output_layer = nn.Linear(10, 10)


	@machine('features')
	def extract_features(self, observation):
		features = self.hidden_layers(observation)
		return features


	@machine('logits')
	def classify_features(self, features):
		logits = self.output_layer(features)
		return logits



def iterative_optimization(model, dataset):

	loader = Loader(dataset, batch_size=32)
	optim = Optimizer(model, lr=0.01)

	for batch in loader:
		batch = model(batch)

		batch = criterion(batch)

		optim.step(batch)

	return model



########################################################################################################################


class Model(nn.Module):
	def __init__(self, observation_space, target_space, nonlin='relu'):
		...

	def forward(self, observation):
		# compute logits from observation
		logits = ...

		return logits


class Dataset(data.Dataset):
	def __init__(self, mode='train'):
		...

	def __getitem__(self, index):
		# load observation and target given the index
		observation = ...
		target = ...
		return observation, target


def criterion(logits, target):
	loss = F.cross_entropy(logits, target)
	return loss


dataset = Dataset(mode='train')
model = Model(nonlin='relu')

loader = Loader(dataset, batch_size=32)
optim = Optimizer(model, lr=0.01)

for batch in loader:  # loads a batch of data
	observation, target = batch

	logit = model(observation)

	loss = criterion(logit, target)

	optim.step(loss)

	accuracy = monitor(logit, target)
	record(accuracy)

save(model)




class Model(nn.Module):
	def __init__(self, **config):
		...

	def forward(self, batch):
		observation = batch['observation']
		batch['logit'] = ...
		return batch


class Dataset(data.Dataset):
	def __init__(self, **config):
		...

	def __getitem__(self, index):
		observation = ...
		target = ...
		batch = {'observation': observation, 'target': target}
		return batch


def criterion(batch):
	observation = batch['observation']
	target = batch['target']
	batch['loss'] = ...
	return batch


dataset_config = {}
model_config = {}
loader_config = {}
optim_config = {}


dataset = Dataset(**dataset_config)
model = Model(**model_config)

loader = Loader(dataset, **loader_config)
optim = Optimizer(model, **optim_config)

for batch in loader:
	batch = model(batch)

	batch = criterion(batch)

	optim.step(batch)

	batch = monitor(batch)
	record(batch)

save(model)




class Model(Structured):
	def __init__(self, **config):
		...

	@machine('logits')
	def classify(self, observation):
		logits = ...
		return logits


class Dataset(data.Dataset):
	def __init__(self, **config):
		...

	@material.sample_from_index('observation')
	def get_observation(self, index):
		observation = ...
		return observation

	@material.sample_from_index('target')
	def get_target(self, index):
		target = ...
		return target



class Model(Structured):
	def __init__(self, **config):
		...

	@machine('features')
	def extract_features(self, observation):
		features = self.hidden_layers(observation)
		return features

	@machine('logits')
	def classify_features(self, features):
		logits = self.output_layer(features)
		return logits




def f_implicit(info):
	x = info.get('x')
	y = info.get('y')
	z = info.get('z')

	# do something
	info['out'] = x + y + z
	return info


def f_eager(x, y, z):
	# do something
	return x + y + z
