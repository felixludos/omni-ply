from .imports import *



class Replicator:
	def _replicator_kwargs(self, kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
		if kwargs is None:
			kwargs = {}
		return kwargs


	def replicate(self, *args, **kwargs) -> Any:
		kwargs = args2kwargs(self.__class__, args, kwargs)
		return self.__class__(**self._replicator_kwargs(kwargs))







