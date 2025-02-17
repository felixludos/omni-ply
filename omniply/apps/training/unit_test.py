from .imports import *

from .datasets import Dataset
from .trainers import TrainerBase



# def test_suggested_batch_size():
#     print()
    
#     dataset_size = 4 * 10 * 10 * 13 * 3 * 3
#     print(dataset_size)

#     best = list(Dataset.suggest_batch_sizes(dataset_size, target_iterations=100))
#     print(best)

#     best = list(Dataset.suggest_batch_sizes(dataset_size, target_batch_size=100))
#     print(best)

#     best = list(Dataset.suggest_batch_sizes(dataset_size, prefer_power_of_two=False, target_iterations=100))
#     print(best)

#     best = list(Dataset.suggest_batch_sizes(dataset_size, prefer_power_of_two=False, target_batch_size=100))
#     print(best)



def test_dataset():
    import numpy as np

    class _Toy(Dataset):
        @tool('even')
        def even(self, index) -> bool:
            return index % 2 == 0
        
        @property
        def size(self) -> int:
            return 12
        
    print()

    toy = _Toy()
    print(toy)
    print(toy.size)

    for batch in toy.iterate(3):
        # print(batch)
        # print(batch['index'])
        print(batch['even'])
        print(batch)
    


def test_trainer():
    import numpy as np

    class _Trainer(TrainerBase):
        def learn(self, batch):
            print(f'learning with loss={batch.grab("loss"):.2g}')
            return batch


    @tool('loss')
    def loss(a, b) -> float:
        return np.linalg.norm(a - b)
    

    class _Toy(Dataset):
        def __init__(self, N: int = 20, **kwargs):
            super().__init__(**kwargs)
            self._A = np.random.randn(N)
            self._B = np.random.randn(N)
        
        @property
        def size(self) -> int:
            return len(self._A)

        @tool('a')
        def a(self, index) -> float:
            return self._A[index]
        
        @tool('b')
        def b(self, index) -> float:
            return self._B[index]


    print()

    toy = _Toy()
    trainer = _Trainer()
    trainer.include(loss)

    for batch in trainer.fit_loop(toy, max_epochs=1):
        print(f'after learn step with {batch.size} samples ({batch["index"]})')





    




