



class ExtractionError(ValueError):
	def __init__(self, obj):
		super().__init__(obj)
		self.obj = obj



class UnknownObjectError(TypeError):
	pass



class NoObjectError(AttributeError):
	pass












