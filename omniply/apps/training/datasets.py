from .imports import *
from .abstract import AbstractDataset
from .batches import Batch
from .planners import Indexed



class Dataset(ToolKit, AbstractDataset):
    _Planner = Indexed
    _Batch = Batch
    def iterate(self, batch_size: Optional[int] = None) -> Iterator[Batch]:
        if batch_size is None:
            batch_size = 1
        
        planner = self._Planner(self, max_epochs=1, shuffle=False, hard_budget=True, drop_last=False)

        for info in planner.generate(batch_size):
            batch = self._Batch(info, planner=planner, allow_draw=False)
            yield batch.include(self)

