import sys, os
import yaml

import torch
from torch import nn

from omnibelt import unspecified_argument, agnostic
import omnifig as fig

import omnidata as od
from omnidata import toy
# from omnidata import Builder, Buildable, RegistryBuilder, MultiBuilder
from omnidata import hparam, inherit_hparams, submodule, spaces

def _cmp_dicts(d1, d2):
	return yaml.dump(d1, sort_keys=True) == yaml.dump(d2, sort_keys=True)
























