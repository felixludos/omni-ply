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
        
        planner = self._Planner(dataset_size=self.size, max_epochs=1, shuffle=False, hard_budget=True, drop_last=False)
        
        try:
            while True:
                batch = self._Batch(planner.step(batch_size), planner=planner, allow_draw=False)
                batch.include(self)
                yield batch
        except planner._BudgetExceeded:
            pass

