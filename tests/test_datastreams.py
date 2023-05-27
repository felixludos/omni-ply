import sys, os
import yaml

# import torch

import omniplex as od
from omniplex import toy
from omniplex.data import BudgetLoader

def _cmp_dicts(d1, d2):
	return yaml.dump(d1, sort_keys=True) == yaml.dump(d2, sort_keys=True)


datastream = None

def _init_default_datastream():
	global datastream
	if datastream is None:
		datastream = toy.Helix(seed=16283393149723337453)
	return datastream



def test_datastream_init():
	datastream = _init_default_datastream()

	assert str(datastream) == 'Helix(observation, target, manifold)'

	buffers = tuple(sorted(datastream.gizmos()))
	# assert len(buffers) == len(datastream)
	assert buffers == ('manifold', 'observation', 'target')

	assert str(datastream.observation_space) \
	       == 'Joint(Bound(min=-1, max=1), Bound(min=-1, max=1), Bound(min=-1, max=1))'
	assert str(datastream.target_space) == 'Categorical(2)'
	assert str(datastream.manifold_space) == 'Joint(Bound(min=-1, max=1), Categorical(2))'

	assert datastream.observation_space.shape == (3,)
	assert datastream.target_space.shape == ()
	assert datastream.manifold_space.shape == (2,)



def test_datastream_fingerprint():
	datastream = _init_default_datastream()

	assert datastream.fingerprint.code() == '2088833c49e45aaa8ab0fe8837b8cb15'

	assert _cmp_dicts(datastream.fingerprint.data(),
	                  {'cls': 'Helix',
	                   'module': 'omnidata.data.toy.manifolds',
	                   'w': 1.0, 'Rz': 1.0, 'Ry': 1.0, 'Rx': 1.0,
	                   'periodic_strand': False, 'n_helix': 2})



def test_datastream_prepare():
	datastream = _init_default_datastream()

	assert datastream.is_ready == False

	datastream.prepare()

	assert datastream.is_ready == True



def test_datastream_iteration():
	datastream = toy.Helix().prepare()

	loader = BudgetLoader(datastream, batch_size=5, batch_limit=3)
	assert loader.remaining_batches == 3
	assert loader.remaining_samples == 15

	assert loader.current_batch is None

	batch = next(loader)
	assert str(batch) == 'Bunch[5]<Helix>({observation}, {target}, {manifold})'

	assert batch.progress is loader

	assert loader.batch_count == 1
	assert loader.sample_count == 5

	assert loader.remaining_samples == 10
	assert loader.remaining_batches == 2


	loader = BudgetLoader(datastream, batch_size=5, sample_limit=16)
	assert not loader.done()
	assert tuple(batch.size for batch in loader) == (5, 5, 5, 5)
	assert loader.done()
	assert loader.batch_count == 4
	assert loader.sample_count == 20

	loader = BudgetLoader(datastream, batch_size=5, sample_limit=16, strict_batch_size=True)
	assert tuple(batch.size for batch in loader) == (5, 5, 5, 5)
	assert loader.batch_count == 4
	assert loader.sample_count == 20

	loader = BudgetLoader(datastream, batch_size=5, sample_limit=16, strict_batch_size=True, strict_limit=True)
	assert tuple(batch.size for batch in loader) == (5, 5, 5)
	assert loader.batch_count == 3
	assert loader.sample_count == 15

	loader = BudgetLoader(datastream, batch_size=5, sample_limit=16, strict_limit=True)
	assert tuple(batch.size for batch in loader) == (5, 5, 5, 1)
	assert loader.batch_count == 4
	assert loader.sample_count == 16



def test_datastream_batch():
	datastream = _init_default_datastream()

	batch = datastream.batch(10, seed=1001)

	assert str(batch) == 'Bunch[10]<Helix>({observation}, {target}, {manifold})'

	buffers = tuple(sorted(batch.gizmos()))
	# assert len(buffers) == len(batch)
	assert buffers == ('manifold', 'observation', 'target')


	assert str(batch.space_of('observation')) \
	       == 'Joint(Bound(min=-1, max=1), Bound(min=-1, max=1), Bound(min=-1, max=1))'
	assert str(batch.space_of('target')) == 'Categorical(2)'
	assert str(batch.space_of('manifold')) == 'Joint(Bound(min=-1, max=1), Categorical(2))'

	assert tuple(batch.cached()) == ()

	obs = batch['observation']
	assert obs.shape == (10, 3)
	assert obs.dtype == torch.float32
	assert obs.sum().item() == 0.9631270170211792

	assert tuple(sorted(batch.cached())) == ('manifold', 'observation')


















