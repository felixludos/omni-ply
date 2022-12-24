
from omnibelt import agnostic, unspecified_argument

from ..features import Prepared

from .hyperparameters import ConfigHyperparameter, InheritableHyperparameter
from .parameterized import ParameterizedBase, ModifiableParameterized, FingerprintedParameterized
from .building import ConfigBuilder, AutoBuilder, BuildableBase, ModifiableProduct, \
	MultiBuilderBase, AutoRegistryBuilderBase, ClassBuilderBaseAuto
from .machines import MachineBase
from .spec import PreparedParameterized, Specced


class Hyperparameter(InheritableHyperparameter, ConfigHyperparameter):
	pass


class Machine(Hyperparameter, MachineBase):
	pass



class Parameterized(ModifiableParameterized, Specced, PreparedParameterized, FingerprintedParameterized):
	Hyperparameter = Hyperparameter
	Machine = Machine



class BasicBuilder(ConfigBuilder, AutoBuilder, Parameterized): # not recommended as it can't handle modifiers
	pass

class Builder(ModifiableProduct, BasicBuilder, inheritable_auto_methods=['product_base']):
	pass

class Buildable(BuildableBase, Builder):
	pass

class MultiBuilder(Builder, MultiBuilderBase, BasicBuilder, wrap_existing=True):
	@agnostic
	def product_base(self, *args, **kwargs):
		return super(ModifiableProduct, self).product(*args, **kwargs)

class RegistryBuilder(MultiBuilder, AutoRegistryBuilderBase, create_registry=False):
	'''
	Important note: __init__ should not have any positional arguments,
	except for `ident` when instantiating a builder
	'''
	pass

class ClassBuilder(RegistryBuilder, ClassBuilderBaseAuto, create_registry=False):
	pass
















