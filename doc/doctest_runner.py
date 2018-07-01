"""Wraps doctest execution"""

import doctest

if __name__ == "__main__":
    import rflow.core
    doctest.testmod(rflow.core)

    import rflow._reflection
    doctest.testmod(rflow._reflection)

