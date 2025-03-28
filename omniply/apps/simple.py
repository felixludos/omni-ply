from typing import Any, Iterator, Callable, Optional
from collections import UserDict
from omnibelt import filter_duplicates

# from collections import frozenset

from ..core import AbstractGame
from ..core.gadgets import GadgetBase
from ..core.genetics import GeneticGadget



class DictGadget(GeneticGadget):
	def __init__(self, data: dict[str, Any], **kwargs):
		super().__init__(**kwargs)
		self.data = data


	def __delitem__(self, key):
		raise NotImplementedError


	def __getitem__(self, item):
		if item in self.data:
			return self.data[item]
		raise KeyError(f'Key not found: {item}')


	def gizmos(self) -> Iterator[str]:
		yield from self.data.keys()


	def _genetic_information(self, gizmo: str):
		info = super()._genetic_information(gizmo)
		info['parents'] = []
		return info


	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
		return self[gizmo]



class Table(GeneticGadget):
	'''
	note that table does not call load() automatically,
	that has to be done manually or in a subclass (eg. with staging)
	'''
	_index_gizmo = 'index'
	_index_attribute = None
	_columns = None

	def __init__(self, data_in_columns: dict[str, list[Any]] = None, **kwargs):
		super().__init__(**kwargs)
		assert self._index_gizmo is None or self._index_attribute is None, \
			f'Cannot specify both index_gizmo and index_attribute'
		self.data = data_in_columns
		self._loaded_data = data_in_columns is not None


	@property
	def is_loaded(self):
		return self._loaded_data


	def load(self):
		if not self.is_loaded:
			self.data = self._load_data()
			self._loaded_data = self.data is not None
		return self


	def _load_data(self) -> dict[str, list[Any]]:
		raise NotImplementedError


	@property
	def columns(self) -> list[str]:
		if self._columns is None and self.is_loaded:
			self._columns = tuple(self.data)
		return self._columns


	@property
	def number_of_rows(self) -> int:
		if self.is_loaded:
			return len(self.data[self.columns[0]])


	def grab_from(self, ctx: 'AbstractGame', gizmo: str) -> Any:
		# self.load()
		index = ctx.grab(self._index_gizmo) if self._index_attribute is None else getattr(ctx, self._index_attribute)
		return self.data[gizmo][index]


	def gizmos(self) -> Iterator[str]:
		# self.load()
		yield from self.columns


	def _genetic_information(self, gizmo: str) -> Iterator[str]:
		info = super()._genetic_information(gizmo)
		info['parents'] = [self._index_gizmo] if self._index_attribute is None else []
		return info


	def __len__(self):
		if not self.is_loaded:
			raise ValueError(f'Cannot determine length of unloaded table (run load() first)')
		return self.number_of_rows


	def __getitem__(self, index: int):
		self.load()
		return {col: self.data[col][index] for col in self.columns}


	def getvalue(self, col: str, index: int) -> Any:
		return self.data[col][index]


	def __repr__(self):
		rows = self.number_of_rows
		cols = self.columns

		terms = [f'{self.__class__.__name__}']
		if rows:
			terms.append(f'[{rows}]')
		if cols:
			terms.append(f'({", ".join(cols)})')
		return ''.join(terms)


	def __str__(self):
		return repr(self)


	@staticmethod
	def _validate_rows(rows: list[dict[str, Any]]) -> dict[str, list[Any]]:
		assert len(rows), f'Cannot create table from empty rows'
		cols = frozenset(col for row in rows for col in row)
		assert all(frozenset(row) == cols for row in rows), f'Inconsistent columns'
		return {col: [row[col] for row in rows] for col in rows[0]}


	@staticmethod
	def _validate_columns(columns: dict[str, list[Any]]) -> dict[str, list[Any]]:
		assert len(columns), f'Cannot create table from empty columns'
		lens = [len(col) for col in columns.values()]
		assert all(lens[0] == l for l in lens), f'Inconsistent column lengths'
		return columns.copy()



# flags and conds
from ..core import tool
from ..core.tools import AutoToolCraft, ToolCraftBase, ToolSkill, ToolDecoratorBase
from ..core.genetics import AutoFunctionGadget



class AutoFlagCraft(AutoFunctionGadget, ToolCraftBase):
	class _ToolSkill(AutoFunctionGadget, ToolSkill): # note that technically `ToolSkill` is MIMO
		def _grab_from(self, ctx):
			return super()._grab_from(ctx) or ctx.grab(self._gizmo, False)


class flag(ToolDecoratorBase):
	_ToolCraft = AutoFlagCraft



class AutoCondCraft(AutoFunctionGadget, ToolCraftBase):
	class _ToolSkill(AutoFunctionGadget, ToolSkill):
		def _grab_from(self, ctx):
			return super()._grab_from(ctx) and ctx.grab(self._gizmo, False)


class cond(ToolDecoratorBase):
	_ToolCraft = AutoCondCraft


# TODO: flags and conds from_context
# TODO: implement gapped flags and conds










