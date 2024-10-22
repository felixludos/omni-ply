from .imports import *
from .abstract import AbstractMogul, AbstractDataset, AbstractGoal
from .goals import Indexed

# Array = Union[list, np.ndarray, torch.Tensor]



class IndexSelector(ToolKit):
    def __init__(self, selection: Iterable[int]):
        super().__init__()
        self._selection = selection


    @tool('index')
    def get_index(self, index: Iterable[int]) -> Iterable[int]:
        return index[self._selection]



class SubsetSelector(Scope):
    def __init__(self, source: Context, selection: Iterable[int], **kwargs):
        super().__init__(**kwargs)
        self._source = source
        self._selection = selection


    def _grab(self, gizmo: str):
        return self._source.grab(gizmo)[self._selection]



class Subset(ToolKit):
    def __init__(self, source: Context, selection: Iterable[int], *, index_key='index', gap=None, **kwargs):
        if gap is None: gap = {}
        if index_key is not None and index_key != 'index':
            gap['index'] = index_key
        super().__init__(gap=gap, **kwargs)
        self._selection = selection
        self._selector = SubsetSelector(source, selection)


    @tool('index')
    def get_index(self, index: Iterable[int]) -> Iterable[int]:
        return index[self._selection]
    


class IndexViewer(ViewerBase):
    def _grab_from_source(self, gizmo: str):
        full = self._source.grab(gizmo)
        if len(full) == self._source.size:
            return full[self._selection]
        return full



class Dataset(AbstractDataset):
    _Planner = Indexed
    def iterate(self, cond: Union[int, ] = None, /, **settings: Any) -> Iterator[AbstractGame]:
        if isinstance(cond, int):
            size = self.size
            if size is None:
                while True:
                    yield 
            else:
                assert cond <= size, f'batch size is too large: max is {size}'
                planner = self._Planner(dataset_size=size, batch_size=cond, **settings)
                


        raise NotImplementedError
    
    pass



class Batch(Context, AbstractDataset):
    def __init__(self, meta: AbstractGoal):
        super().__init__()
        self._meta = meta
        
    @property
    def meta(self) -> AbstractGoal:
        return self._meta

    @property
    def size(self) -> int:
        return self.meta['size']

    def _new_given_meta(self, meta: AbstractGoal) -> 'Batch':
        new = self.gabel()
        new._meta = meta
        return new

    def new(self, size: int = None) -> 'Batch':
        return self._new_given_meta(self.meta.new(size=size))













