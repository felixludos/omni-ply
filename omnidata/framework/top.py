
from omnibelt import agnostic, unspecified_argument
from .features import Prepared
from .hyperparameters import ConfigHyperparameter
from .building import ConfigBuilder, AutoBuilder, BuildableBase, ModifiableProduct, \
	MultiBuilderBase, RegistryBuilderBase, ClassBuilderBase
from .parameterized import ParameterizedBase
from .machines import MachineBase


class Hyperparameter(ConfigHyperparameter):
	pass


class Machine(Hyperparameter, MachineBase):
	pass



class MachineParameterized(ParameterizedBase):
	Machine = MachineBase

	@classmethod
	def register_machine(cls, name=None, _instance=None, **kwargs):
		_instance = cls.Machine(name=name, **kwargs) if _instance is None else cls.Machine.extract_from(_instance)
		if name is None:
			name = _instance.name
		return cls._register_hparam(name, _instance)

	@agnostic
	def machines(self):
		for key, val in self.named_machines():
			yield val

	@agnostic
	def named_machines(self):
		for key, val in self.named_hyperparameters():
			if isinstance(val, MachineBase):
				yield key, val


class PreparedParameterized(MachineParameterized, Prepared):
	@agnostic
	def _prepare_machine(self, name, machine, **kwargs):
		val = getattr(self, name, None)
		if isinstance(val, Prepared):
			val.prepare(**kwargs)


	@agnostic
	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)
		for name, machine in self.named_machines():
			self._prepare_machine(name, machine)

	@agnostic
	def reset(self):
		self._prepared = False
		self.reset_hparams()


class Parameterized(PreparedParameterized):
	Hyperparameter = Hyperparameter
	Machine = Machine



class BasicBuilder(ConfigBuilder, AutoBuilder, Parameterized): # not recommended as it can't handle modifiers
	pass

class Builder(ModifiableProduct, BasicBuilder, inheritable_auto_methods=['product_base']):
	pass

class Buildable(BuildableBase, Builder):
	pass

class MultiBuilder(Builder, MultiBuilderBase, wrap_existing=True):
	@agnostic
	def product_base(self, *args, **kwargs):
		return super(ModifiableProduct, self).product(*args, **kwargs)

class RegistryBuilder(MultiBuilder, RegistryBuilderBase):
	pass

class ClassBuilder(RegistryBuilder, ClassBuilderBase):
	pass
















