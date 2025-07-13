
class GemError(Exception):
	pass

class NoNameError(GemError):
	"raised if a gem is created without a name"
	pass

class NoValueError(GemError):
	"raised if neither a function nor a default value is provided for a gem"
	pass


class RevisionsNotAllowedError(GemError):
	"raised if a gem is not allowed to be revised"
	pass


class ResolutionLoopError(GemError):
	"raised if a gem depends on another gem that is currently being resolved"
	pass

# class MissingQuirkValue(ValueError):
# 	pass
