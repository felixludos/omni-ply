from .abstract import AbstractArgumentBuilder
from .hyperparameters import InheritableHyperparameter
from .parameterized import ModifiableParameterized, FingerprintedParameterized, InheritHparamsDecorator, HparamWrapper
from .building import ConfigBuilder, BuildableBase, MultiBuilderBase, RegistryBuilderBase, HierarchyBuilderBase, RegisteredProductBase
from .submodules import SubmoduleBase
# from .spec import PreparedParameterized, SpeccedBase, BuilderSpecced, StatusSpec, BuildableSpec



class hparam(InheritableHyperparameter):
	pass



class submodule(SubmoduleBase):
	pass



class inherit_hparams(InheritHparamsDecorator):
	pass



class with_hparam(HparamWrapper):
	pass


# class Hyperparameter(InheritableHyperparameter, ConfigHyperparameter):
# 	pass
#
#
# class Submodule(Hyperparameter, SubmoduleBase):
# 	pass


# class Spec(StatusSpec, BuildableSpec):
# 	# TODO: spec -> config (and config -> spec (?))
# 	pass



# class Parameterized(SpeccedBase, ModifiableParameterized, FingerprintedParameterized, PreparedParameterized):
class Parameterized(ModifiableParameterized, FingerprintedParameterized):
	pass



# not recommended as it can't handle modifiers



# class BasicBuilder(ConfigBuilder, BuilderSpecced, Parameterized): # AutoBuilder
# 	pass



class Builder(Parameterized):#(ConfigBuilder, Parameterized):
	#, inheritable_auto_methods=['product_base']):
	pass



class Buildable(Builder, BuildableBase):
	pass



class MultiBuilder(Builder, MultiBuilderBase):#, wrap_existing=True):
	pass



class RegistryBuilder(Builder, RegistryBuilderBase, create_registry=False):
	pass



class HierarchyBuilder(RegistryBuilder, HierarchyBuilderBase, create_registry=False):
	pass



class RegisteredProduct(Buildable, RegisteredProductBase):
	pass



class MatchingBuilder(Parameterized, AbstractArgumentBuilder):
	'''Automatically fills in common hyperparameters between the builder and the product'''
	fillin_hparams = hparam(True, inherit=True, hidden=True)
	fillin_hidden_hparams = hparam(False, inherit=True, hidden=True)


	def _matching_hparams(self, product):
		known = set(key for key, _ in self.named_hyperparameters())
		for key, _ in product.named_hyperparameters(hidden=self.fillin_hidden_hparams):
			if key in known:
				yield key


	def _build_kwargs(self, product, *args, **kwargs):
		kwargs = super()._build_kwargs(product, *args, **kwargs)
		if self.fillin_hparams:
			for key in self._matching_hparams(product):
				if key not in kwargs:
					try:
						val = getattr(self, key)
					except AttributeError:
						continue
					else:
						kwargs[key] = val
		return kwargs













