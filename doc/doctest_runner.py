"""Wraps doctest execution"""

import doctest

if __name__ == "__main__":
    import rflow.core
    doctest.testmod(rflow.core)
