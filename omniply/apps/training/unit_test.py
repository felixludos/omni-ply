from .imports import *

from .datasets import Dataset




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
        print(batch)
        print(batch['index'])
        print(batch['even'])
    


    




