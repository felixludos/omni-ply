from .imports import *



class NoOptionsError(Exception):
	pass



class IgnoreCase(Exception):
	'''
	used to signal to a decision that it should not defer to a case to make a choice,
	and instead just default to the standard behavior (usually meaning the decision
	will choose itself)
	'''
	pass


