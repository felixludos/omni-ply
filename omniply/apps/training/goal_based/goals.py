from ..imports import *
from ..abstract import AbstractMogul, AbstractDataset, AbstractGoal



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






