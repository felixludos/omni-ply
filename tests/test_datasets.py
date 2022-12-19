
import sys, os
import yaml
import omnidata as od
from omnidata import toy

dataset = None

def _init_default_dataset():
	global dataset
	if dataset is None:
		dataset = toy.SwissRollDataset(100, seed=16283393149723337453)
	return dataset

def _cmp_dicts(d1, d2):
	return yaml.dump(d1, sort_keys=True) == yaml.dump(d2, sort_keys=True)



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

	assert dataset.fingerprint.code() == '7ecef17fca79acae08a429ec6fb26544'

	assert _cmp_dicts(dataset.fingerprint.data(),
	                  {'cls': 'SwissRollDataset',
	                   'module': 'omnidata.data.toy.manifolds',
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
	dataset = _init_default_dataset()


	progression = dataset.iterate()

	assert len(progression) == 10


	pass



def test_dataset_batch():
	dataset = _init_default_dataset()

	batch = dataset.batch(10)

	assert str(batch) == 'Batch[10]{SwissRollDataset[100]}({observation}, {target}, {mechanism})'

	buffers = tuple(sorted(batch.available()))
	assert len(buffers) == len(batch)
	assert buffers == ('mechanism', 'observation', 'target')

	assert str(batch.observation_space) \
	       == 'Joint(Bound(min=-14.1, max=14.1), Bound(min=0, max=21), Bound(min=-14.1, max=14.1))'
	assert str(batch.target_space) == 'Bound(min=3, max=9)'
	assert str(batch.mechanism_space) == 'Joint(Bound(min=3, max=9), Bound(min=0, max=1))'

	assert tuple(batch.cached()) == ()

	obs = batch['observation']
	assert obs.shape == (10, 3)
	assert obs.dtype == 'float32'
	assert obs.sum().item() == 100.31050872802734

	assert tuple(sorted(batch.cached())) == ('mechanism', 'observation')


















