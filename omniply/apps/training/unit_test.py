from .imports import *

from .datasets import Dataset




def test_suggested_batch_size():
    print()
    
    dataset_size = 4 * 10 * 10 * 13 * 3 * 3
    print(dataset_size)

    best = list(Dataset.suggest_batch_sizes(dataset_size, target_iterations=100))
    print(best)

    best = list(Dataset.suggest_batch_sizes(dataset_size, target_batch_size=100))
    print(best)

    best = list(Dataset.suggest_batch_sizes(dataset_size, prefer_power_of_two=False, target_iterations=100))
    print(best)

    best = list(Dataset.suggest_batch_sizes(dataset_size, prefer_power_of_two=False, target_batch_size=100))
    print(best)



