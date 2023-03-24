from ..tools import Industrial
from .abstract import AbstractArgumentBuilder
from .hyperparameters import InheritableHyperparameter
from .parameterized import ModifiableParameterized, FingerprintedParameterized, InheritHparamsDecorator, \
	InheritableParameterized, HparamWrapper, SpatialParameterized
from .building import ConfigBuilder, BuilderBase, BuildableBase, MultiBuilderBase, RegistryBuilderBase, \
	HierarchyBuilderBase, RegisteredProductBase, ModifiableProduct, AnalysisBuilder
from .submodules import SubmoduleBase, SubmachineBase
from .spec import ArchitectBase, Specced, SpecBase, PlannedBase
# from .spec import PreparedParameterized, SpeccedBase, BuilderSpecced, StatusSpec, BuildableSpec



class hparam(InheritableHyperparameter):
	pass



class submodule(SubmoduleBase):
	pass



class submachine(SubmachineBase):
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




class Parameterized(SpatialParameterized, ModifiableParameterized,
                    InheritableParameterized, FingerprintedParameterized):
	pass



class Spec(SpecBase):
	pass
PlannedBase._Spec = Spec



# class Parameterized(SpeccedBase, ModifiableParameterized, FingerprintedParameterized, PreparedParameterized):
class Structured(Parameterized, Specced):
	@classmethod
	def inherit_hparams(cls, *names):
		out = super().inherit_hparams(*names)
		for name in names:
			val = getattr(cls, name, None)
			if isinstance(val, submachine) and len(cls._inherited_tool_relabels):
				setattr(cls, name, val.replace(cls._inherited_tool_relabels))
		return out
	pass



# not recommended as it can't handle modifiers



# class BasicBuilder(ConfigBuilder, BuilderSpecced, Parameterized): # AutoBuilder
# 	pass


class Builder(ModifiableProduct, ArchitectBase, AnalysisBuilder):#(ConfigBuilder, Parameterized):
	#, inheritable_auto_methods=['product_base']):

	def _build_kwargs(self, product, *args, **kwargs):
		kwargs = super()._build_kwargs(product, *args, **kwargs)
		if issubclass(product, Industrial) and 'application' not in kwargs and self._application is not None:
			kwargs['application'] = self._application
		return kwargs




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



class MatchingBuilder(Structured, AbstractArgumentBuilder):
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













