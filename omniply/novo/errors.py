from omniply.core.abstract import *


class ApplicationAmbiguityError(ValueError):
	def __init__(self, gizmo: str, options: Sequence[str], *, message: Optional[str] = None):
		if message is None:
			message = f'{gizmo!r} cant choose between: {options}'
		super().__init__(message)
		self.gizmo = gizmo
		self.options = options



class MissingValueError(AttributeError):
	def __init__(self, descriptor: Any, message: Optional[str] = None):
		if message is None:
			message = f'{descriptor}'
		super().__init__(message)



class MissingOwnerError(TypeError):
	def __init__(self, descriptor: Any, message: Optional[str] = None):
		if message is None:
			message = f'Cannot delete {descriptor} without providing an instance.'
		super().__init__(message)



class ReachFailedFlag(Exception):
	def __init__(self):
		super().__init__('to access this "realize()" is necessary')



class IgnoreResetFlag(Exception):
	pass



class GadgetFailedError(AbstractGadgetError):
	def __init__(self, gizmo: str, *, message: Optional[str] = None):
		if message is None:
			message = f'{gizmo!r}'
		super().__init__(message)
		self.gizmo = gizmo


	def reason(self):
		return f'{self.gizmo!r} {self.__class__.__name__}'



class AssemblyFailedError(GadgetFailedError):
	def __init__(self, gizmo: str, *failures: GadgetFailedError,
                 message: Optional[str] = None):
		if message is None:
			message = self.verbalize_failures(gizmo, failures)
		super().__init__(gizmo, message=message)
		self.gizmo = gizmo
		self.failures = failures


	def reason(self):
		return f'{self.gizmo} [{", ".join(f.reason() if isinstance(f, GadgetFailedError) else repr(f) for f in self.failures)}]'


	@staticmethod
	def verbalize_failures(gizmo: str, failures: Sequence[GadgetFailedError]):
		# path = [repr(e.gizmo) for e in failures]
		# terminal = failures[-1].reason()
		reason = f'[{", ".join(f.reason() if isinstance(f, GadgetFailedError) else repr(f) for f in failures)}]'
		return f'{gizmo!r} due to {reason}'



class MissingGizmoError(GadgetFailedError, KeyError):
	def __init__(self, gizmo: str, *, message: Optional[str] = None):
		if message is None:
			message = gizmo
		super().__init__(gizmo, message=message)


	def reason(self):
		return f'missing {self.gizmo!r}'



# class SkipToolFlag(ToolFailedError):
# 	'''raised by a tool to indicate that it should be skipped'''
# 	pass









