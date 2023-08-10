from .imports import *
from .errors import *


class AbstractBlueprint:
	pass



class AbstractArtist:
	def details(self) -> Dict[str, Any]:
		raise NotImplementedError


	def derivative(self, *args, **kwargs) -> 'AbstractArtist':
		'''Returns a new artist that is a derivative of this one (ie. same except for the given args, and kwargs).'''
		raise NotImplementedError


	@agnostic
	def draft(self, *args, **kwargs) -> Type: # aka "product"
		if isinstance(self, type):
			return self(*args, **kwargs).design()
		return self._design()


	@agnostic
	def describe(self, *args, **kwargs): # aka "plan"
		pass


	@agnostic
	def develop(self, *args, **kwargs): # aka "build"
		pass


	@agnostic
	def design(self, *args, **kwargs): # aka "draft"
		pass


	def _design(self):
		pass


	def _develop(self):
		raise NotImplementedError



class Artist(AbstractArtist, Replicator):
	def derivative(self, *args, **kwargs) -> 'AbstractArtist':
		'''Returns a new artist that is a derivative of this one (ie. same except for the given args, and kwargs).'''
		kwargs = args2kwargs(self.__class__, args, kwargs)
		return self.replicate(**kwargs)



class AbstractArchitect(AbstractArtist):
	def design_with(self, blueprint: Any):
		raise NotImplementedError


	def design_for(self, owner: Any) -> Any:
		raise NotImplementedError



























