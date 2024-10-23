from .imports import *
from .abstract import AbstractDataset
from .batches import Batch
from .planners import Indexed



def prime_factors(n: int, /): # should probably be moved to omnibelt
    from sympy import nextprime
    # Handle edge case for n <= 1
    if n <= 1:
        raise ValueError("n must be greater than 1")
    prime = 2

    # Iterate over prime factors using sympy's nextprime function
    while prime * prime <= n:
        # While the current prime divides n, add it to the list and divide n
        while n % prime == 0:
            yield prime
            n //= prime
        # Get the next prime number
        prime = nextprime(prime)

    # If n is still greater than 2, it must be a prime number
    if n > 2:
        yield n



def closest_factors(A_factors: Union[int, Iterable[int], dict[int, int]], B_factors: Union[int, list[int], dict[int, int]], /):
    """
    Generate factors of A in order such that they are closest to B.

    ref: https://chatgpt.com/c/67176426-7d0c-8005-85cb-f89dc96a5db3

    Parameters:
    - A_factors: dict mapping primes to their exponents in the factorization of A
    - B_factors: dict mapping primes to their exponents in the factorization of B

    Yields:
    - factors of A in order, starting from those closest to B
    """

    if isinstance(A_factors, int):
        A_factors = prime_factors(A_factors)
    if isinstance(B_factors, int):
        B_factors = prime_factors(B_factors)
    if not isinstance(A_factors, dict):
        A_factors = Counter(A_factors)
    if not isinstance(B_factors, list):
        B_factors = Counter(B_factors)

    # Get the list of primes in A
    primes = list(A_factors.keys())
    n = len(primes)

    # Build exponent vectors for A and B
    E_A = [A_factors[p] for p in primes]
    E_B = [B_factors.get(p, 0) for p in primes]

    # Initial exponent vector: min(E_B[i], E_A[i])
    initial_e = tuple(min(E_B[i], E_A[i]) for i in range(n))

    # Compute the initial factor f = product(p_i ** e_i)
    initial_f = 1
    for p, e in zip(primes, initial_e):
        initial_f *= p ** e

    # Compute the target value B_value
    B_value = 1
    for p, e in B_factors.items():
        B_value *= p ** e

    # Compute the initial delta
    initial_delta = abs(initial_f - B_value)

    # Initialize the priority queue
    heap = []
    heapq.heappush(heap, (initial_delta, initial_f, initial_e))

    # Initialize the visited set
    visited = set()
    visited.add(initial_e)

    # Begin the search
    while heap:
        delta, f, e = heapq.heappop(heap)
        yield f  # Yield the current factor

        # Generate neighboring exponent vectors
        for i in range(n):
            e_list = list(e)

            # Try incrementing e_i if it's less than E_A[i]
            if e[i] < E_A[i]:
                e_list[i] += 1
                e_inc = tuple(e_list)
                if e_inc not in visited:
                    f_inc = f * primes[i]
                    delta_inc = abs(f_inc - B_value)
                    heapq.heappush(heap, (delta_inc, f_inc, e_inc))
                    visited.add(e_inc)

            e_list = list(e)

            # Try decrementing e_i if it's greater than 0
            if e[i] > 0:
                e_list[i] -= 1
                e_dec = tuple(e_list)
                if e_dec not in visited:
                    f_dec = f // primes[i]
                    delta_dec = abs(f_dec - B_value)
                    heapq.heappush(heap, (delta_dec, f_dec, e_dec))
                    visited.add(e_dec)



def suggest_batch_sizes(dataset_size: int, *, 
                        prefer_power_of_two: bool = True,
                        target_iterations: Optional[int] = 100, 
                        target_batch_size: Optional[int] = None) -> Iterator[int]:
    '''
    yields perfectly divisible batch sizes in order of closeness to target_batch_size 
    (or s.t. there are target_iterations if not provided)

    if prefer_power_of_two is True, it will first yield the best power of two
    '''
    if dataset_size is None:
        yield 32
        return

    assert target_batch_size is not None or target_iterations is not None, 'either target_batch_size or target_iterations must be provided'
    if target_batch_size is None:
        target_batch_size = dataset_size // target_iterations
    assert 0 < target_batch_size <= dataset_size, 'target_batch_size must be in (0, dataset_size]' 

    factors = Counter(prime_factors(dataset_size))
    if prefer_power_of_two and 2 in factors:
        yield min((2 ** i for i in range(1,factors[2] + 1)), key=lambda x: abs(x - target_batch_size))

    yield from closest_factors(factors, Counter(prime_factors(target_batch_size)))



class Dataset(ToolKit, AbstractDataset):
    _Planner = Indexed
    _Batch = Batch
    def iterate(self, batch_size: Optional[int] = None) -> Iterator[Batch]:
        if batch_size is None:
            batch_size = 1
        
        planner = self._Planner(dataset_size=self.size, max_epochs=1, hard_budget=True, drop_last=False)
        
        try:
            while True:
                batch = self._Batch(planner.step(batch_size), planner=planner, allow_draw=False)
                batch.include(self)
                yield batch
        except planner._BudgetExceeded:
            pass

    
    def suggest_batch_size(self, *, prefer_power_of_two: bool = True, 
                            target_iterations: Optional[int] = 100, 
                            target_batch_size: Optional[int] = None) -> int:
        return next(suggest_batch_sizes(self.size, prefer_power_of_two=prefer_power_of_two, 
                                       target_iterations=target_iterations, target_batch_size=target_batch_size))


