import sys, os
import yaml

import torch

import omnidata as od
from omnidata import toy

def _cmp_dicts(d1, d2):
	return yaml.dump(d1, sort_keys=True) == yaml.dump(d2, sort_keys=True)


dataset = None

def _init_default_dataset():
	global dataset
	if dataset is None:
		dataset = toy.SwissRollDataset(100, batch_size=5, seed=16283393149723337453)
	return dataset

def test_dataset_init():
	dataset = _init_default_dataset()

	assert dataset.size == 100

	assert str(dataset) == 'SwissRollDataset[100](observation, target, mechanism)'

	buffers = tuple(sorted(dataset.available()))
	assert len(buffers) == len(dataset)
	assert buffers == ('mechanism', 'observation', 'target')

	assert str(dataset.observation_space) \
	       == 'Joint(Bound(min=-14.1, max=14.1), Bound(min=0, max=21), Bound(min=-14.1, max=14.1))'
	assert str(dataset.target_space) == 'Bound(min=3, max=9)'
	assert str(dataset.mechanism_space) == 'Joint(Bound(min=3, max=9), Bound(min=0, max=1))'

	assert dataset.observation_space.shape == (3,)
	assert dataset.target_space.shape == ()
	assert dataset.mechanism_space.shape == (2,)


def test_dataset_fingerprint():
	dataset = _init_default_dataset()

	assert dataset.fingerprint.code() == 'dbe51ff6144ae53dadb46e33553c1a3d'

	assert _cmp_dicts(dataset.fingerprint.data(),
	                  {'cls': 'SwissRollDataset',
	                   'module': 'omnidata.data.toy.manifolds',
	                   'batch_size': 5,
	                   'tmax': 9.0, 'tmin': 3.0, 'freq': 0.5,
	                   'Az': 1.5707963267948966, 'Ay': 21.0, 'Ax': 1.5707963267948966,
	                   'n_samples': 100
	                   })


def test_dataset_prepare():
	dataset = _init_default_dataset()

	assert dataset.is_ready == False

	dataset.prepare()

	assert dataset.is_ready == True


def test_dataset_iteration():
	dataset = toy.SwissRollDataset(12, batch_size=5).prepare()

	loader = dataset.iterate(epochs=1).prepare()
	assert loader.remaining_batches == 3

	assert loader.current_batch is None

	batch = loader.get_batch()
	assert str(batch) == 'Batch[5]<SwissRollDataset[12]>({observation}, {target}, {mechanism})'

	assert batch.progress is loader

	assert loader.batch_count == 1
	assert loader.sample_count == 5
	assert loader.current_epoch == 1

	assert loader.remaining_samples == 7
	assert loader.remaining_batches == 2


	loader = dataset.iterate(sample_limit=16).prepare()
	assert not loader.done
	assert tuple(batch.size for batch in loader) == (5, 5, 2, 5)
	assert loader.done
	assert loader.batch_count == 4
	assert loader.sample_count == 17
	assert loader.current_epoch == 2

	loader = dataset.iterate(sample_limit=16, strict_batch_size=True).prepare()
	assert tuple(batch.size for batch in loader) == (5, 5, 5, 5)
	assert loader.batch_count == 4
	assert loader.sample_count == 20
	assert loader.current_epoch == 2

	loader = dataset.iterate(sample_limit=16, strict_batch_size=True, strict_limit=True).prepare()
	assert tuple(batch.size for batch in loader) == (5, 5, 5)
	assert loader.completed_epochs == 1
	assert loader.batch_count == 3
	assert loader.sample_count == 15
	assert loader.current_epoch == 2


	loader = dataset.iterate(sample_limit=16, strict_limit=True).prepare()
	assert tuple(batch.size for batch in loader) == (5, 5, 2, 4)
	assert loader.batch_count == 4
	assert loader.sample_count == 16
	assert loader.current_epoch == 2



def test_dataset_batch():
	dataset = _init_default_dataset()

	batch = dataset.batch(10)

	assert str(batch) == 'Batch[10]<SwissRollDataset[100]>({observation}, {target}, {mechanism})'

	buffers = tuple(sorted(batch.available()))
	assert len(buffers) == len(batch)
	assert buffers == ('mechanism', 'observation', 'target')

	assert str(batch.space_of('observation')) \
	       == 'Joint(Bound(min=-14.1, max=14.1), Bound(min=0, max=21), Bound(min=-14.1, max=14.1))'
	assert str(batch.space_of('target')) == 'Bound(min=3, max=9)'
	assert str(batch.space_of('mechanism')) == 'Joint(Bound(min=3, max=9), Bound(min=0, max=1))'

	assert tuple(batch.cached()) == ()

	obs = batch['observation']
	assert obs.shape == (10, 3)
	assert obs.dtype == torch.float32
	assert obs.sum().item() == 92.62188720703125

	assert tuple(sorted(batch.cached())) == ('observation',)


















