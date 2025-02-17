from .imports import *
from .abstract import AbstractDataset, AbstractBatch, AbstractPlanner



class NoNewBatches(Exception):
    pass



class BatchInfo(DictGadget):
    pass



class Batch(Context, AbstractBatch):
    _BatchInfo = BatchInfo
    def __init__(self, info: dict[str, Any], *, planner: AbstractPlanner, allow_draw: bool = True, **kwargs):
        if isinstance(info, dict):
            info = self._BatchInfo(info)
        super().__init__(**kwargs)
        self._info = info
        self._planner = planner
        self._allow_draw = allow_draw
        self.include(info)
        

    def gadgetry(self) -> Iterator[AbstractGadget]:
        for gadget in self.vendors():
            if gadget is not self._info:
                yield gadget


    @property
    def size(self) -> int:
        return self.grab('size')


    def _new(self, size: int = None, *, planner=None, allow_draw=None, **kwargs) -> 'Batch':
        if planner is None:
            planner = self._planner
        if allow_draw is None:
            allow_draw = self._allow_draw
        if size is None:
            size = self.size
        new = self.__class__(planner.draw(size), planner=planner, allow_draw=allow_draw, **kwargs)
        new.extend(tuple(self.gadgetry()))
        return new


    def new(self, size: int = None) -> 'Batch':
        if self._allow_draw:
            return self._new(size)
        raise NoNewBatches(f'creating new batches using the current batch is currently not allowed')





