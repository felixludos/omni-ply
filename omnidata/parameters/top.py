
from omnibelt import agnostic, unspecified_argument

from ..features import Prepared

from .hyperparameters import ConfigHyperparameter, InheritableHyperparameter
from .parameterized import ModifiableParameterized, FingerprintedParameterized
from .building import ConfigBuilder, AutoBuilder, BuildableBase, SelfAware, ModifiableProduct, \
	MultiBuilderBase, RegistryBuilderBase, RegisteredProductBase
from .machines import MachineBase
from .spec import PreparedParameterized, SpeccedBase, BuilderSpecced, StatusSpec, BuildableSpec


class Hyperparameter(InheritableHyperparameter, ConfigHyperparameter):
	pass


class Machine(Hyperparameter, MachineBase):
	pass


class Spec(StatusSpec, BuildableSpec):
	# TODO: spec -> config (and config -> spec (?))
	pass



class Parameterized(SpeccedBase, ModifiableParameterized, PreparedParameterized, FingerprintedParameterized):
	Hyperparameter = Hyperparameter
	Machine = Machine
	Spec = Spec


# not recommended as it can't handle modifiers

class BasicBuilder(ConfigBuilder, AutoBuilder, BuilderSpecced, Parameterized):
	pass

class Builder(ModifiableProduct, BasicBuilder, inheritable_auto_methods=['product_base']):
	pass

class Buildable(SelfAware, Builder):
	pass



class MultiBuilder(Builder, MultiBuilderBase, BasicBuilder, wrap_existing=True):
	@agnostic
	def product_base(self, *args, **kwargs):
		return super(ModifiableProduct, self).product(*args, **kwargs)



class RegistryBuilder(MultiBuilder, RegistryBuilderBase, create_registry=False):
	pass

class RegisteredProduct(Buildable, RegisteredProductBase):
	pass

















