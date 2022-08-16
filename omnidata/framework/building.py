import inspect
from omnibelt import agnosticmethod, unspecified_argument, Class_Registry, extract_function_signature
from .hyperparameters import Parametrized, ModuleParametrized, hparam, inherit_hparams


class Builder(ModuleParametrized):
	
	def _extract_(self, fn, args, kwargs):
		def defaults(n):
			if n in self._registered_hparams:
				return getattr(self, n)
			raise KeyError(n)
		
		return extract_function_signature(fn, args, kwargs, defaults)


	def expected_hparams(self, items=True):
		return self.iterate_hparams(items)


	@agnosticmethod
	def build(self, *args, **kwargs):
		fixed_args, fixed_kwargs = self._extract_(self._build, args, kwargs)
		return self._build(*fixed_args, **fixed_kwargs)
	
	
	@staticmethod
	def _build(*args, **kwargs):
		raise NotImplementedError



class BuilderRegistry(Class_Registry):
	def get_builder(self, name):
		return self.find(name).cls
builder_registry = BuilderRegistry()
register_builder = builder_registry.get_decorator()
get_builder = builder_registry.get_builder



class ClassBuilder(Builder):
	

	def get_possible_classes(self):
		return self._registered_hparams.keys()




	
	pass



