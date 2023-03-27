
import numpy as np

from omnidata import hparam, inherit_hparams, submodule, submachine, spaces
from omnidata import Guru, Context, material, space, indicator, machine, Structured



class Rifleman(Structured): # Eg 1
	@material.from_size('captain')
	def generate_captains_order(self, N):
		return np.random.rand(N) < 0.5 # Bernoulli(0.5) prior

	@machine('rifleman1')
	def rifleman1_shoots(self, captain):
		return captain

	@machine('rifleman2')
	def rifleman2_shoots(self, captain):
		return captain

	@machine('prisoner')
	def prisoner_dies(self, rifleman1, rifleman2):
		return rifleman1 | rifleman2



def test_rifleman():

	ctx = Guru(Rifleman(), size = 10)

	print(ctx['prisoner'])
	print(ctx['captain'])

	assert np.all(ctx['prisoner']==ctx['captain'])



def test_rifleman2():

	ctx = Guru(Rifleman(), size = 10)

	ctx['captain'] = True # "intervention"

	print(ctx['prisoner'])

	assert ctx['prisoner']

	ctx.clear()

	ctx['captain'] = False

	print(ctx['prisoner'])

	assert not ctx['prisoner']


	ctx.clear()

	ctx['captain'] = False
	ctx['rifleman1'] = True

	print(ctx['prisoner'])

	assert ctx['prisoner']



class MediatorGraph(Structured):
	@material.from_size('X')
	def generate_independent_variable(self, N):
		return np.random.rand(N) < 0.5

	@machine('Z')
	def mediator_variable(self, X):
		if isinstance(X, bool): # for some reason bitwise ops don't work on bools :/
			return not X
		return ~X

	@machine('Y')
	def dependent_variable(self, X, Z):
		return X | Z



def test_mediator():

	ctx = Guru(MediatorGraph(application = {'X': 'man', 'Z': 'wax', 'Y': 'dark'}), size = 10)

	ctx['man'] = True

	print(ctx['wax'])
	print(ctx['dark'])

	assert not ctx['wax']
	assert ctx['dark']



class SimpleLinearMediator(Structured):
	'''
	Linear mediator model

	X = U1
	Z = aX + U2
	Y = bX + cZ + U3

	'''

	a = hparam()
	b = hparam()
	c = hparam()

	@material.from_size('U1')
	@material.from_size('U2')
	@material.from_size('U3')
	def generate_exogenous(self, N):
		return np.random.randn(N)


	@machine('X')
	def independent_variable(self, U1):
		return U1

	@machine('Z')
	def mediator_variable(self, X, U2):
		return self.a * X + U2

	@machine('Y')
	def dependent_variable(self, X, Z, U3):
		return self.b * X + self.c * Z + U3


	# abduction

	@machine('aU1')
	def aU1(self, X):
		'''Abduction for U1'''
		return X

	@machine('aU2')
	def aU2(self, X, Z):
		'''Abduction for U2'''
		return Z - self.a * X

	@machine('aU3')
	def aU3(self, X, Z, Y):
		'''Abduction for U3'''
		return Y - self.b * X - self.c * Z



class SimpleNonlinearMediator(Structured):
	'''
	Nonlinear mediator model (with additive noise)

	X = U1
	Z = aX + U2
	Y = X * Z + U3

	'''

	a = hparam()

	@material.from_size('U1')
	@material.from_size('U2')
	@material.from_size('U3')
	def generate_exogenous(self, N):
		return np.random.randn(N)


	@machine('X')
	def independent_variable(self, U1):
		return U1

	@machine('Z')
	def mediator_variable(self, X, U2):
		return self.a * X + U2

	@machine('Y')
	def dependent_variable(self, X, Z, U3):
		return X * Z + U3


	@machine('aU1')
	def aU1(self, X):
		'''Abduction for U1'''
		return np.roots([1,self.independent_variable(-X)])

	@machine('aU2')
	def aU2(self, X, Z):
		'''Abduction for U2'''
		return np.roots([1, self.mediator_variable(X, -Z)])

	@machine('aU3')
	def aU3(self, X, Z, Y):
		'''Abduction for U3'''
		return np.roots([1, self.dependent_variable(X, Z, -Y)])



def create_counterfactual(factual, interventions):
	'''
	converts a factual into a counterfactual with the given interventions

	abductions must be specified in the model "prefix a" (eg "aU1" for "U1")
	'''
	abduction = {f'U{i+1}': factual[f'aU{i+1}'] for i in range(3)}

	factual.clear() # reset state

	factual.update(abduction) # set exogenous variables
	factual.update(interventions)

	return factual # now this is the counterfactual



def test_counterfactual():

	factual = Guru(SimpleLinearMediator(a=0.5, b=0.7, c=0.4), size = 1)

	factual.update({'X': 0.5, 'Z': 1, 'Y': 1.5})

	counterfactual = create_counterfactual(factual, {'Z': 2})

	assert counterfactual['X'] == 0.5
	assert counterfactual['Z'] == 2
	assert counterfactual['Y'] == 1.9






