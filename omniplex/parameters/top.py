from omnibelt.crafts import HiddenCrafty

from ..tools import Industrial, SignatureCraft, Signature
from .abstract import AbstractArgumentBuilder
from .hyperparameters import InheritableHyperparameter
from .parameterized import ModifiableParameterized, FingerprintedParameterized, InheritHparamsDecorator, \
	InheritableParameterized, HparamWrapper, SpatialParameterized
from .building import ConfigBuilder, BuilderBase, MultiBuilderBase, RegistryBuilderBase, \
	HierarchyBuilderBase, ModifiableProduct, AnalysisBuilder, RegisteredProductBase
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
class Structured(Specced, Parameterized):
	@classmethod
	def inherit_hparams(cls, *names):
		out = super().inherit_hparams(*names)
		for name in names:
			val = getattr(cls, name, None)
			if isinstance(val, submachine) and len(cls._inherited_tool_relabels):
				setattr(cls, name, val.replace(cls._inherited_tool_relabels))
		return out



class Function(Structured, HiddenCrafty):
	_auto_machine = SignatureCraft
	def __init_subclass__(cls, signature: Signature = None, **kwargs):
		super().__init_subclass__(**kwargs)
		if signature is not None:
			if signature.fn is None:
				signature.fn = getattr(cls, '__call__', None)
			cls._hidden_crafts.append(cls._auto_machine(signature))



class SimpleFunction(Function):
	_Signature = Signature
	def __init_subclass__(cls, inputs=None, output=None, metas=None, signature=None, **kwargs):
		if signature is None:
			signature = cls._Signature(inputs=inputs, output=output, metas=metas)
		super().__init_subclass__(signature=signature, **kwargs)



# not recommended as it can't handle modifiers



# class BasicBuilder(ConfigBuilder, BuilderSpecced, Parameterized): # AutoBuilder
# 	pass



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
		if self.fillin_hparams and issubclass(product, Parameterized):
			for key in self._matching_hparams(product):
				if key not in kwargs:
					try:
						val = getattr(self, key)
					except AttributeError:
						continue
					else:
						kwargs[key] = val
		return kwargs



class Builder(MatchingBuilder, ArchitectBase, ModifiableProduct, AnalysisBuilder):#(ConfigBuilder, Parameterized):
	#, inheritable_auto_methods=['product_base']):
	pass



# class Buildable(Builder, BuildableBase):
# 	pass



class MultiBuilder(MultiBuilderBase, Builder):#, wrap_existing=True):
	pass



class RegistryBuilder(RegistryBuilderBase, Builder, create_registry=False):
	pass



class HierarchyBuilder(HierarchyBuilderBase, RegistryBuilder, create_registry=False):
	pass



class RegisteredProduct(Structured, RegisteredProductBase):
	pass











