from .imports import *
from .abstract import AbstractDataset, AbstractPlanner
from .batches import Batch, Frame
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



class FrameSet(ToolKit, AbstractDataset):
    class _Planner(AbstractPlanner):
        def __init__(self, src: AbstractDataset, *, shuffle: bool = None, seed: int = None,
                     index_key: str = 'index', **kwargs):
            super().__init__(**kwargs)
            self._src = src
            self._index_key = index_key
            if shuffle:
                indices = list(range(src.size))
                random.Random(seed).shuffle(indices)
            else:
                indices = None
            self._indices = indices
            self._offset = 0
            self._num_iterations = 0


        def draw(self, size: int = 1) -> Dict[str, Any]:
            assert size == 1, f'Collection planner only supports size=1, not {size}'
            data = {self._index_key: self._offset if self._indices is None else self._indices[self._offset]}
            self._offset += 1
            return data


        def step(self, size: int = 1) -> Dict[str, Any]:
            assert size == 1, f'Collection planner only supports size=1, not {size}'
            self._num_iterations += 1
            return self.draw()


        def generate(self, size: int = 1) -> Iterator[Dict[str, Any]]:
            assert size == 1, f'Collection planner only supports size=1, not {size}'
            while self._offset < self._src.size:
                yield self.step()


    _Batch = Frame
    def iterate(self, *, shuffle: Optional[bool] = None, allow_draw: bool = True) -> Iterator[Batch]:
        planner = self._Planner(self, shuffle=shuffle)
        for info in planner.generate():
            batch = self._Batch(info, planner=planner, allow_draw=allow_draw)
            yield batch.include(self)






