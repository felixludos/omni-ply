import sys, os
import yaml

import torch
from torch import nn

from omnibelt import unspecified_argument, agnostic
import omnifig as fig

import omnidata as od
from omnidata import toy
from omnidata.tools import Guru, Context, Industrial, material, space, indicator, machine
from omnidata.tools.assessments import SimpleAssessment


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














