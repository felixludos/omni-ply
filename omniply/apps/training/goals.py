from .imports import *
from .abstract import AbstractMogul, AbstractDataset, AbstractGoal



class GoalBase(Context, AbstractGoal):
    def new(self, size: int = None) -> AbstractGoal:
        new = self.gabel()
        if size is not None:
            new.include(DictGadget({'size': size}))
        return new
    

    @property
    def size(self) -> int:
        return self['size']



class Goal(GoalBase):
    def __init__(self, budget: Indexed = None, **kwargs):
        super().__init__(**kwargs)
        self._budget = budget


    @property
    def budget(self) -> Indexed:
        return self._budget
    

    def is_achieved(self) -> bool:
        return self.budget


    def new(self, size: int = None) -> AbstractGoal:
        new = super().new(size=size)
        new._budget = self._budget
        return new



class Sized(ToolKit):
    def __init__(self, batch_size: int, **kwargs):
        super().__init__(**kwargs)
        self._batch_size = batch_size


    @tool('size')
    def get_size(self) -> int:
        return self._batch_size



class Indexed(ToolKit):
    def __init__(self, batch_size: int = None, dataset_size: int = None, *, 
                 shuffle: bool = True, multi_epoch: bool = True, **kwargs):
        super().__init__(**kwargs)
        self._dataset_size = dataset_size
        self._batch_size = batch_size
        self._shuffle = shuffle
        self._multi_epoch = multi_epoch
        self.reset()


    def set_dataset_size(self, size: int):
        self._dataset_size = size
        return self


    def reset(self):
        self._order = None
        self._offset = 0

        self._drawn_samples = 0
        self._drawn_batches = 0
        self._drawn_epochs = 0


    def draw(self, n: int):
        import numpy as np

        if self._order is None:
            self._order = np.random.permutation(self._dataset_size) if self._shuffle else np.arange(self._dataset_size)
            self._offset = 0
            self._drawn_epochs += 1

        assert self._multi_epoch or n < len(self._order), f'batch size is too large: max is {len(self._order)}'

        if self._offset + n > len(self._order):
            prev = self._order[self._offset:]
            self._order = None
            self._drawn_samples += len(self._order) - self._offset
            if self._multi_epoch:
                return np.concatenate((prev, self.draw(n - len(prev))))
            self._drawn_batches += 1
            return prev
        
        batch = self._order[self._offset:self._offset + n]
        self._offset += n
        self._drawn_samples += n
        self._drawn_batches += 1
        return batch


    @tool('index')
    def get_index(self, size: int) -> Iterable[int]:
        assert self._dataset_size is not None, 'dataset size is not set'
        return self.draw(size)
    

    @tool('samples')
    def get_samples(self, index: Iterable[int]) -> int:
        return self._drawn_samples
    

    @tool('batches')
    def get_batches(self) -> int:
        return self._drawn_batches
    
    
    @tool('epochs')
    def get_epochs(self) -> int:
        return self._drawn_epochs


class BudgetExceeded(Exception):
    pass


class Budgeter(Indexed):
    def __init__(self, dataset_size: int = None, *, 
                 max_epochs: int = None, max_samples: int = None, max_batches: int = None, 
                 max_steps: int = None, max_iterations: int = None, **kwargs):
        super().__init__(dataset_size=dataset_size, **kwargs)
        self._max_epochs = max_epochs
        self._max_samples = max_samples
        self._max_batches = max_batches
        self._max_steps = max_steps
        self._max_iterations = max_iterations


    def reset(self):
        self._num_iterations = 0
        return super().reset()


    _BudgetExceeded = BudgetExceeded
    def draw(self, n: int):
        if self._max_samples is not None and self._drawn_samples + n > self._max_samples:
            raise self._BudgetExceeded('max samples exceeded')
        if self._max_batches is not None and self._drawn_batches + 1 > self._max_batches:
            raise self._BudgetExceeded('max batches exceeded')
        idx = super().draw(n)
        if self._max_epochs is not None and self._drawn_epochs > self._max_epochs:
            raise self._BudgetExceeded('max epochs exceeded')
        return idx
    

    def step(self):
        self._num_iterations += 1
        if self._max_steps is not None and self._num_iterations > self._max_steps:
            raise self._BudgetExceeded('max steps exceeded')
        return self
    

    @tool('samples_remaining')
    def get_samples_remaining(self, samples: int) -> int:
        return self._max_samples - samples


    @tool('iterations')
    def get_iterations(self) -> int:
        return self._num_iterations





