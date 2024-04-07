from typing import Any, Optional
from omnibelt import pformat, pformat_vars, pathfinder

from ..core import AbstractGame
from ..core.gadgets import SingleGadgetBase



class Template(SingleGadgetBase):
	def __init__(self, template: str, gizmo: str = None, **kwargs):
		super().__init__(gizmo=gizmo, **kwargs)
		self._template = template
		self._keys = None


	@property
	def keys(self):
		if self._keys is None:
			self._keys = self._parse_keys(self.template)
		return self._keys
	@property
	def template(self):
		return self._template


	@staticmethod
	def _parse_keys(template):
		return list(pformat_vars(template))


	def fill_in(self, reqs: dict[str, str] = None, **vals: str):
		return pformat(self.template, reqs, **vals)


	def _grab_from(self, ctx: Optional[AbstractGame]) -> Any:
		reqs = {key: ctx.grab_from(ctx, key) for key in self.keys}
		return self.fill_in(reqs)



class FileTemplate(Template):
	_find_template_path = pathfinder(default_suffix='txt', must_exist=True, validate=lambda p: p.is_file())

	def __init__(self, template_name: str = None, *, template_path=None, template=None, **kwargs):
		if template_name is not None or template_path is not None:
			template_path = self._find_template_path(template_name, path=template_path)
			template = template_path.read_text()
		super().__init__(template=template, **kwargs)
		self.template_path = template_path







