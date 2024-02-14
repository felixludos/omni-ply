import sys, os
import yaml

import random
# import torch
# from torch import nn

from omnibelt import unspecified_argument, agnostic
import omnifig as fig

import omniplex as od
from omniplex import toy
from omniplex.tools import Guru, Context, Industrial, material, space, indicator, machine
from omniplex.tools.assessments import SimpleAssessment


class Simple(Industrial):
	@machine('b')
	def f(self, a):
		return a + 1



class Simple2(Industrial):
	@machine('c')
	def f(self, a, b):
		return a + b

	@machine('d')
	def g(self, c):
		return c + 1


class Simple3(Industrial):
	@material.from_size('x')
	def f(self, N):
		return torch.arange(N)

	@material.from_indices('y')
	def g(self, indices):
		return indices

	@material.next_sample('z')
	def h(self):
		return -1

	@material.sample_from_index('w')
	def i(self, index):
		return index

	# @space('x')
	# def x_space(self, y):
	# 	return torch.zeros(y.shape)



def test_industrial():
	s = Simple()
	assert s.f(1) == 2



def test_tool_init():
	g = Guru(Simple(), Simple2())

	g['a'] = 1
	assert g['b'] == 2
	assert g['c'] == 3
	assert g['d'] == 4



def test_tool_analysis():
	g = Guru(Simple2(), Simple())

	sig = list(g.signatures())

	print()
	print('\n'.join(map(str, sig)))

	assert len(sig) == 3



def test_simple_materials():
	g = Guru(Simple3())

	print()
	print('\n'.join(map(str, g.signatures())))


	assert g['z'] == -1

	g.index = 5
	assert g['w'] == 5

	g._size = 10
	assert g['x'].shape == (10,)

	g.indices = [1,2,3]
	assert g['y'] == [1,2,3]



class Q1(Industrial):
	@material.from_size('x')
	def f1(self, N):
		return N



class Q2(Q1):
	@machine('y')
	def g2(self, x):
		return x + 1

	@machine('z')
	def h2(self, x, y):
		return x + y



class Q3(Industrial):
	@machine('y')
	def g3(self, x):
		return x + 1

	@machine('z')
	def h3(self, x, y):
		return x + y



def test_simple_industry():
	g = Guru(Q3(), Q1(), size=1)

	print()
	print('\n'.join(map(str, g.signatures())))

	assert g['x'] == 1
	assert g['y'] == 2
	assert g['z'] == 3



def test_simple_inheritance():
	g = Guru(Q2(), size=1)

	print()
	print('\n'.join(map(str, g.signatures())))

	assert g['x'] == 1
	assert g['y'] == 2
	assert g['z'] == 3



class Q4(Q3, replace={'y':'y2'}):
	@machine('z')
	def g4(self, y2):
		return y2 + 1

	@machine('y')
	def h4(self):
		return 15



def test_simple_relabel():
	g = Guru(Q4(), Q1(), size=1)

	print()
	print('\n'.join(map(str, g.signatures())))

	assert g['x'] == 1
	assert g['y'] == 15
	assert g['y2'] == 2
	assert g['z'] == 3











