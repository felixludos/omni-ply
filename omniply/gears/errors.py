from .imports import *
from ..core.errors import GadgetFailed, GrabError, SkipGadget


class MissingMechanicsError(Exception):
	'''raised when a gear is missing mechanics'''
	pass


class GearFailed(GadgetFailed):
	'''alias for gadget failed, no change in behavior'''
	pass


class SkipGear(GearFailed, SkipGadget):
	pass


class GearGrabError(GrabError):
	pass
