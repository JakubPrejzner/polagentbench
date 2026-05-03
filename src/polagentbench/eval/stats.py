"""Statistical helpers for the adversarial-suite analysis.

Two functions, both stdlib-only (no scipy):

* :func:`bootstrap_ci` — percentile bootstrap confidence interval on the
  mean of a list of binary outcomes. Used to put error bars on per-condition
  pass rates so a 7/9 vs 8/9 split isn't read as a real difference.
* :func:`paired_mcnemar` — exact two-sided McNemar test (binomial form) for
  paired binary outcomes. Used to decide whether ``--repair`` produced a
  significant change relative to ``--no-repair`` on the same (task, temp,
  seed) cells.

Both functions are deliberately pure and dependency-free. The bootstrap
takes an optional ``rng_seed`` so tests can pin behaviour; production
callers can pass ``None`` for genuine resampling noise.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence

__all__ = ["bootstrap_ci", "paired_mcnemar"]


def bootstrap_ci(
    success_flags: Sequence[bool],
    *,
    n_resamples: int = 10_000,
    alpha: float = 0.05,
    rng_seed: int | None = 12345,
) -> tuple[float, float]:
    """Percentile-bootstrap CI on the mean of a binary outcome series.

    Args:
        success_flags: Sequence of bools (or ints in {0, 1}); the success
            indicator for each trial.
        n_resamples: Number of bootstrap resamples. Default 10_000.
        alpha: Two-sided significance level — the returned interval covers
            the central ``1 - alpha`` fraction of resampled means.
        rng_seed: Seed for ``random.Random`` so results are reproducible.
            Pass ``None`` to use system randomness.

    Returns:
        ``(lower, upper)`` percentile bounds of the resampled mean.

    Raises:
        ValueError: if ``success_flags`` is empty, ``n_resamples`` < 1, or
            ``alpha`` is not in (0, 1).
    """
    if not success_flags:
        raise ValueError("bootstrap_ci requires at least one observation")
    if n_resamples < 1:
        raise ValueError("n_resamples must be >= 1")
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha must be in (0, 1)")

    flags = [1 if bool(x) else 0 for x in success_flags]
    n = len(flags)

    # Degenerate cases collapse to a point — skip the resampling work.
    s = sum(flags)
    if s == 0:
        return (0.0, 0.0)
    if s == n:
        return (1.0, 1.0)

    rng = random.Random(rng_seed)
    means: list[float] = []
    for _ in range(n_resamples):
        total = 0
        for _i in range(n):
            total += flags[rng.randrange(n)]
        means.append(total / n)

    means.sort()
    lo_idx = int(math.floor((alpha / 2.0) * n_resamples))
    hi_idx = int(math.ceil((1.0 - alpha / 2.0) * n_resamples)) - 1
    lo_idx = max(0, min(lo_idx, n_resamples - 1))
    hi_idx = max(0, min(hi_idx, n_resamples - 1))
    return (means[lo_idx], means[hi_idx])


def paired_mcnemar(
    flags_a: Sequence[bool], flags_b: Sequence[bool]
) -> float:
    """Exact two-sided McNemar test for paired binary outcomes.

    Builds the 2x2 contingency table from element-wise comparison of
    ``flags_a`` and ``flags_b`` (e.g., the same task at the same seed run
    with vs without ``--repair``) and returns a two-sided p-value computed
    from the exact binomial distribution on the discordant pairs.

    Conventional cell labels:

    ===========  ==========  ==========
                 b = pass    b = fail
    a = pass     n11         n10
    a = fail     n01         n00
    ===========  ==========  ==========

    The discordant pairs ``n10`` (a passed, b failed) and ``n01`` (a failed,
    b passed) carry all the information about a paired difference; the test
    is whether ``n10 / (n10 + n01)`` differs from 0.5.

    Args:
        flags_a: First series of binary outcomes.
        flags_b: Second series of binary outcomes (same length as ``flags_a``).

    Returns:
        Exact two-sided p-value in ``[0.0, 1.0]``. Returns 1.0 when there
        are no discordant pairs (no evidence of a difference).

    Raises:
        ValueError: if the two sequences have different lengths or are empty.
    """
    if len(flags_a) != len(flags_b):
        raise ValueError(
            f"paired_mcnemar requires equal-length inputs; got {len(flags_a)} vs {len(flags_b)}"
        )
    if not flags_a:
        raise ValueError("paired_mcnemar requires at least one observation")

    n10 = 0  # a pass, b fail
    n01 = 0  # a fail, b pass
    for a, b in zip(flags_a, flags_b, strict=True):
        a_ok = bool(a)
        b_ok = bool(b)
        if a_ok and not b_ok:
            n10 += 1
        elif (not a_ok) and b_ok:
            n01 += 1

    n_disc = n10 + n01
    if n_disc == 0:
        return 1.0

    k = min(n10, n01)
    # Exact two-sided binomial test at p=0.5: P(K <= k) under Binomial(n_disc, 0.5),
    # doubled for two-sidedness, capped at 1.0.
    tail = 0.0
    for i in range(0, k + 1):
        tail += math.comb(n_disc, i) * (0.5 ** n_disc)
    p_value = min(1.0, 2.0 * tail)
    return p_value
