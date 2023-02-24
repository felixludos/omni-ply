import sys, os
import yaml

import torch
from torch import nn

from omnibelt import unspecified_argument, agnostic
import omnifig as fig

import omnidata as od
from omnidata import toy
from omnidata.tools import Guru, Context, Industrial, material, space, indicator, machine



class Simple(Industrial):
	@machine('a')
	def f(self, b):
		return b + 1





def test_tool_init():

	simple = Simple()

	g = Guru(simple)

	g['b'] = 1
	print(g['a'])
	assert g['a'] == 2















