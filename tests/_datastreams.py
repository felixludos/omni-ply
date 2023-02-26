import sys, os
import yaml

import torch

import omnidata as od
from omnidata import toy

def _cmp_dicts(d1, d2):
	return yaml.dump(d1, sort_keys=True) == yaml.dump(d2, sort_keys=True)


datastream = None

def _init_default_datastream():
	global datastream
	if datastream is None:
		datastream = toy.Helix(batch_size=5, seed=16283393149723337453)
	return datastream


def test_datastream_init():
	datastream = _init_default_datastream()

	assert str(datastream) == 'Helix(observation, target, mechanism)'

	buffers = tuple(sorted(datastream.available_buffers()))
	assert len(buffers) == len(datastream)
	assert buffers == ('mechanism', 'observation', 'target')

	assert str(datastream.observation_space) \
	       == 'Joint(Bound(min=-1, max=1), Bound(min=-1, max=1), Bound(min=-1, max=1))'
	assert str(datastream.target_space) == 'Categorical(2)'
	assert str(datastream.mechanism_space) == 'Joint(Bound(min=-1, max=1), Categorical(2))'

	assert datastream.observation_space.shape == (3,)
	assert datastream.target_space.shape == ()
	assert datastream.mechanism_space.shape == (2,)


def test_datastream_fingerprint():
	datastream = _init_default_datastream()

	assert datastream.fingerprint.code() == '29651650ed8ece4495eac57522f93c07'

	assert _cmp_dicts(datastream.fingerprint.data(),
	                  {'cls': 'Helix',
	                   'module': 'omnidata.data.toy.manifolds',
	                   'batch_size': 5,
	                   'n_helix': 2,
	                   'periodic_strand': False,
	                   'Rx': 1.0,
	                   'Ry': 1.0,
	                   'Rz': 1.0,
	                   'w': 1.0})


def test_datastream_prepare():
	datastream = _init_default_datastream()

	assert datastream.is_ready == False

	datastream.prepare()

	assert datastream.is_ready == True


def test_datastream_iteration():
	datastream = toy.Helix(batch_size=5).prepare()

	loader = datastream.iterate(batch_limit=3).prepare()
	assert loader.remaining_batches == 3
	assert loader.remaining_samples == 15

	assert loader.current_batch is None

	batch = loader.get_batch()
	assert str(batch) == 'Batch[5]<Helix>({observation}, {target}, {mechanism})'

	assert batch.progress is loader

	assert loader.batch_count == 1
	assert loader.sample_count == 5

	assert loader.remaining_samples == 10
	assert loader.remaining_batches == 2


	loader = datastream.iterate(sample_limit=16).prepare()
	assert not loader.done
	assert tuple(batch.size for batch in loader) == (5, 5, 5, 5)
	assert loader.done
	assert loader.batch_count == 4
	assert loader.sample_count == 20

	loader = datastream.iterate(sample_limit=16, strict_batch_size=True).prepare()
	assert tuple(batch.size for batch in loader) == (5, 5, 5, 5)
	assert loader.batch_count == 4
	assert loader.sample_count == 20

	loader = datastream.iterate(sample_limit=16, strict_batch_size=True, strict_limit=True).prepare()
	assert tuple(batch.size for batch in loader) == (5, 5, 5)
	assert loader.batch_count == 3
	assert loader.sample_count == 15

	loader = datastream.iterate(sample_limit=16, strict_limit=True).prepare()
	assert tuple(batch.size for batch in loader) == (5, 5, 5, 1)
	assert loader.batch_count == 4
	assert loader.sample_count == 16


def test_datastream_batch():
	datastream = _init_default_datastream()

	batch = datastream.batch(10)

	assert str(batch) == 'Batch[10]<Helix>({observation}, {target}, {mechanism})'

	buffers = tuple(sorted(batch.available_buffers()))
	assert len(buffers) == len(batch)
	assert buffers == ('mechanism', 'observation', 'target')


	assert str(batch.space_of('observation')) \
	       == 'Joint(Bound(min=-1, max=1), Bound(min=-1, max=1), Bound(min=-1, max=1))'
	assert str(batch.space_of('target')) == 'Categorical(2)'
	assert str(batch.space_of('mechanism')) == 'Joint(Bound(min=-1, max=1), Categorical(2))'

	assert tuple(batch.cached()) == ()

	obs = batch['observation']
	assert obs.shape == (10, 3)
	assert obs.dtype == torch.float32
	assert obs.sum().item() == 1.932597279548645

	assert tuple(sorted(batch.cached())) == ('mechanism', 'observation')


















