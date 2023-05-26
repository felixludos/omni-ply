


class MissingValueError(AttributeError):
	pass



class MissingBuilderError(TypeError):
	pass



class NoProductFound(KeyError):
	pass



class MissingBranchError(NoProductFound):
	def __init__(self, branch, ident, msg=None):
		if msg is None:
			msg = f'Branch {branch!r} not found for ident {ident!r}'
		super().__init__(msg)



class InheritedHparamError(AttributeError):
	pass



class InvalidProductError(TypeError):
	pass

