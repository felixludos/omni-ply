from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Type, Iterable, Iterator
from omnibelt import unspecified_argument, get_printer
from omnibelt.crafts import AbstractCraft

from ..tools.abstract import AbstractScopeGenerator, AbstractScope, AbstractTool, ToolFailedError
from ..tools.assessments import Signatured, AbstractSignature, SimpleSignature
from ..tools.crafts import AbstractCrafty, ToolCraft, ReplaceableCraft
from ..tools.context import SimpleScope

from .abstract import AbstractSubmodule, AbstractModular, AbstractBuilder
from .errors import NoProductFound
from .hyperparameters import HyperparameterBase
from .building import get_builder, BuilderBase

prt = get_printer(__name__)



class SubmoduleBase(HyperparameterBase, AbstractSubmodule): # TODO: check builder for space (if none is provided)
	def __init__(self, default=unspecified_argument, *, typ=None, builder=None, **kwargs):
		super().__init__(default=default, **kwargs)
		# assert typ is None != builder is None, 'Either "typ" or "builder" must be provided'
		self.typ = typ
		self.builder = builder


	def copy(self, *, typ=None, builder=None, **kwargs):
		if typ is None:
			typ = self.typ
		if builder is None:
			builder = self.builder
		return super().copy(typ=typ, builder=builder, **kwargs)


	def init(self, instance):
		# TODO: (future) check for a special fget: spec -> builder for custom builders
		spec = instance.my_blueprint
		if not self.is_cached(instance):
			builder = self._create_default_builder(blueprint=None if spec is None else spec.for_builder())
			setattr(instance, self._default_builder_attr_code.format(self.attrname), builder)


	_default_builder_attr_code = '_temporary_default_builder_for_{}'
	def get_builder(self, owner):
		if isinstance(owner, type):
			return self._create_default_builder()
		if self.is_cached(owner):
			value = getattr(owner, self.attrname)
			if isinstance(value, AbstractBuilder):
				return value
		return getattr(owner, self._default_builder_attr_code.format(self.attrname), None)


	def validate(self, instance):
		value = getattr(instance, self.attrname, unspecified_argument)
		builder = getattr(instance, self._default_builder_attr_code.format(self.attrname), None)

		if builder is None:
			if value is unspecified_argument:
				raise self._MissingValueError(f'No product found for {self.attrname}')
		else:
			spec = instance.my_blueprint
			if spec is None:
				value = builder.build() if value is unspecified_argument else builder.validate(value)
			else:
				value = builder.build_with_spec(spec) if value is unspecified_argument \
					else builder.validate_with_spec(spec, value)
			setattr(instance, self.attrname, value)
			delattr(instance, self._default_builder_attr_code.format(self.attrname))


	_default_builder_type = None # TODO: simple builder that is given the product_base at __init__
	def _create_default_builder(self, *args, **kwargs) -> Optional[BuilderBase]:
		if self.builder is not None:
			builder = get_builder(self.builder) #if isinstance(self.builder, str) else self.builder
			return builder(*args, **kwargs)
		if self.typ is not None:
			return self._default_builder_type(self.typ)
		raise NotImplementedError('no info for default builder was provided') # TODO: make custom error type


	# def build_with(self, *args, **kwargs):
	# 	if self.typ is not None:
	# 		return self.typ(*args, **kwargs)
	# 	builder = self.get_builder()
	# 	if builder is None:
	# 		raise ValueError(f'No builder for {self}')
	# 	return builder.build(*args, **kwargs)
	#
	#
	# def build_with_spec(self, owner, spec):
	# 	builder = self.get_builder(blueprint=spec)
	# 	if builder is None:
	# 		raise ValueError(f'No builder for {self}')
	# 	product = builder.build()
	# 	spec.update_with(builder)
	# 	return product


	# def is_missing(self, owner):
	# 	return not (self.attrname in owner.__dict__ or self.fget is not None)


	# def missing_spaces(self, owner):
	# 	sub = getattr(owner, self.attrname, None)
	# 	if sub is not None:
	# 		yield from sub.missing_spaces()


	# def create_value(self, base, owner=None):  # TODO: maybe make thread-safe by using a lock
	# 	try:
	# 		return super().create_value(base, owner)
	# 	except self.MissingValueError:
	# 		builder = self.get_builder()
	# 		if builder is None:
	# 			raise
	# 		return builder.build()


##############

	# @agnostic
	# def full_spec(self, fmt='{}', fmt_rule='{parent}.{child}', include_machines=True):
	# 	for key, val in self.named_hyperparameters():
	# 		ident = fmt.format(key)
	# 		if isinstance(val, Machine):
	# 			builder = val.get_builder()
	# 			if include_machines or builder is None:
	# 				yield ident, val
	# 			if builder is not None:
	# 				if isinstance(builder, MachineParametrized):
	# 					yield from builder.full_spec(fmt=fmt_rule.format(parent=ident, child='{}'), fmt_rule=fmt_rule)
	# 				else:
	# 					for k, v in builder.plan():
	# 						yield fmt_rule.format(parent=ident, child=k), v
	# 		else:
	# 			yield ident, val



# class submodule(hparam):
# 	_registration_fn_name = 'register_submodule'


class SubmachineTool(ToolCraft, AbstractScopeGenerator):
	class Skill(ToolCraft.Skill):
		def space_of(self, gizmo: str):
			raise self._ToolFailedError(gizmo)


	def __init__(self, label: str, *, attrname=None, signature=None, **kwargs): # label is internal name (may be replaced)
		super().__init__(label, **kwargs)
		self.attrname = attrname
		self.signature = signature


	_Scope = SimpleScope
	def _create_scope(self, ctx, owner, attrname, sub):
		return self._Scope(sub, application=self.replacements)


	# def replace(self, replacements: Dict[str, str], **kwargs): # TODO: remove this
	# 	new = super().replace(replacements, **kwargs)
	# 	# if self.signature is not None:
	# 	# 	new.signature = self.signature.replace(replacements)
	# 	return new

	@property
	def wrapped(self):
		return None


	def _get_from(self, instance: AbstractCrafty, ctx, gizmo: str):
		sub = getattr(instance, self.attrname)

		if isinstance(sub, AbstractTool):
			scope = ctx.scope_for((instance, self.attrname), None)
			if scope is None:
				scope = self._create_scope(ctx, instance, self.attrname, sub)
				if scope is None:
					raise ValueError(f'No scope for {instance} and {self.attrname}')
				ctx.register_scope((instance, self.attrname), scope)

			return scope.get_from(ctx, gizmo)

		elif self.signature is not None:
			return self._automatic_get_from(sub, self.signature.replace(self.replacements), ctx)

		raise ToolFailedError(gizmo)


	def _automatic_get_from(self, sub, sig, ctx):
		if len(sig.inputs):
			vals = [ctx[inp] for inp in sig.inputs]
			return sub(*vals)
		elif 'size' in sig.meta:
			return sub(ctx.size)
		elif 'indices' in sig.meta:
			return sub(ctx.indices)
		elif 'index' in sig.meta:
			return sub(ctx.index)
		raise ToolFailedError(sig.output)


	def signatures(self, owner: Type[AbstractCrafty] = None):
		if self.signature is None:
			yield from super().signatures(owner)
		else:
			yield self.signature.replace(self.replacements, name=self.attrname)



class SubmachineBase(SubmoduleBase, Signatured, ReplaceableCraft):
	_Tool = SubmachineTool
	def __init__(self, default=unspecified_argument, *, application=None, replacements=None, **kwargs):
		if replacements is None:
			replacements = application
		if 'label' in kwargs:
			del kwargs['label'] # TODO: add warning about this
		# if 'replacements' in kwargs:
		# 	raise NotImplementedError('SubmachineBase does not support "replacements" (use "application" instead)')
		super().__init__(default=default, label=None, replacements=replacements, **kwargs)


	def copy(self, *, replacements=None, label=None, **kwargs):
		if replacements is None:
			replacements = self.replacements
		if label is None:
			label = self.label
		return super().copy(replacements=replacements, label=label, **kwargs)


	_default_builder_type = None # TODO: simple builder that is given the product_base at __init__
	def _create_default_builder(self, *args, application=None, **kwargs) -> Optional[BuilderBase]:
		if application is None:
			application = self.replacements
		return super()._create_default_builder(*args, application=application, **kwargs)


	def _expected_signatures(self, owner=None):
		if not isinstance(owner, type) and self.is_cached(owner):
			value = getattr(owner, self.attrname)
			if isinstance(value, Signatured):
				yield from value.signatures()
				return
		builder = self.get_builder(owner)
		if builder is not None:
			yield from builder.product_signatures()


	def emit_craft_items(self, owner=None):
		if self.replacements is not None:
			for signature in self._expected_signatures(owner=owner):
				if signature.output in self.replacements:
					yield self._Tool(signature.output, attrname=self.attrname, replacements=self.replacements,
					                 signature=signature)








