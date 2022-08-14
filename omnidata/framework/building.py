import inspect
from omnibelt import agnosticmethod, unspecified_argument, Class_Registry
from .hyperparameters import Parametrized, ModuleParametrized, hparam, inherit_hparams


class Builder(ModuleParametrized):
	@agnosticmethod
	def build(self, *args, **kwargs):
		params = inspect.signature(self._build).parameters
		
		arg_idx = 0
		fixed_args = []
		fixed_kwargs = {}
		
		for n, p in params.items():
			if p.kind == p.POSITIONAL_ONLY:
				if arg_idx < len(args):
					fixed_args.append(args[arg_idx])
					arg_idx += 1
				elif n in self._registered_hparams:
					fixed_args.append(getattr(self, n))
			elif p.kind == p.VAR_POSITIONAL:
				if n in self._registered_hparams:
					fixed_args.extend(getattr(self, n))
				else:
					fixed_args.extend(args[arg_idx:])
					arg_idx = len(args)
			elif p.kind == p.KEYWORD_ONLY:
				if n in kwargs:
					fixed_kwargs[n] = kwargs[n]
				elif n in self._registered_hparams:
					fixed_kwargs[n] = getattr(self, n)
			elif p.kind == p.VAR_KEYWORD:
				if n in self._registered_hparams:
					fixed_kwargs.update(getattr(self, n))
				else:
					fixed_kwargs.update(kwargs)
		
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




