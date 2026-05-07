"""Tests for bootstrap_ci and paired_mcnemar."""

from __future__ import annotations

import math

import pytest

from polagentbench.eval.stats import bootstrap_ci, paired_mcnemar

# ---------------------------------------------------------------------------
# bootstrap_ci
# ---------------------------------------------------------------------------


def test_bootstrap_ci_all_success_collapses_to_one():
    lo, hi = bootstrap_ci([True] * 10)
    assert (lo, hi) == (1.0, 1.0)


def test_bootstrap_ci_all_fail_collapses_to_zero():
    lo, hi = bootstrap_ci([False] * 10)
    assert (lo, hi) == (0.0, 0.0)


def test_bootstrap_ci_brackets_observed_mean():
    flags = [True] * 7 + [False] * 3  # mean = 0.7
    lo, hi = bootstrap_ci(flags, n_resamples=2000)
    assert lo <= 0.7 <= hi
    # CI should be reasonably wide for n=10 — at least 0.3 spread.
    assert hi - lo >= 0.3


def test_bootstrap_ci_tightens_with_more_data():
    flags_small = [True, True, True, False] * 2  # n=8, mean 0.75
    flags_large = [True, True, True, False] * 50  # n=200, same mean
    lo_s, hi_s = bootstrap_ci(flags_small, n_resamples=2000)
    lo_l, hi_l = bootstrap_ci(flags_large, n_resamples=2000)
    assert (hi_l - lo_l) < (hi_s - lo_s)


def test_bootstrap_ci_reproducible_with_same_seed():
    flags = [True, False, True, False, True, True, False] * 3
    a = bootstrap_ci(flags, n_resamples=500, rng_seed=42)
    b = bootstrap_ci(flags, n_resamples=500, rng_seed=42)
    assert a == b


def test_bootstrap_ci_empty_input_raises():
    with pytest.raises(ValueError, match="at least one observation"):
        bootstrap_ci([])


def test_bootstrap_ci_invalid_alpha_raises():
    with pytest.raises(ValueError, match="alpha"):
        bootstrap_ci([True, False], alpha=1.5)


def test_bootstrap_ci_invalid_n_resamples_raises():
    with pytest.raises(ValueError, match="n_resamples"):
        bootstrap_ci([True, False], n_resamples=0)


def test_bootstrap_ci_accepts_int_flags():
    lo, hi = bootstrap_ci([1, 1, 1, 0, 0])
    assert 0.0 <= lo <= hi <= 1.0


# ---------------------------------------------------------------------------
# paired_mcnemar
# ---------------------------------------------------------------------------


def test_mcnemar_identical_inputs_return_one():
    p = paired_mcnemar([True, False, True, False], [True, False, True, False])
    assert p == 1.0


def test_mcnemar_no_discordant_pairs_return_one():
    """Both series differ in *content* but not in any paired position."""
    a = [True, True, False, False]
    b = [True, True, False, False]
    assert paired_mcnemar(a, b) == 1.0


def test_mcnemar_full_flip_yields_significant_p():
    """All 10 cells flip from fail->pass under treatment B."""
    a = [False] * 10
    b = [True] * 10
    p = paired_mcnemar(a, b)
    # 10 discordant pairs all in one direction => 2 * 0.5**10 = ~0.00195
    assert p < 0.01
    assert math.isclose(p, 2.0 * 0.5 ** 10, rel_tol=1e-9)


def test_mcnemar_one_flip_in_each_direction_is_max_p():
    """1 cell A>B and 1 cell B>A — symmetric, p should be 1.0."""
    a = [True, False] + [False] * 8
    b = [False, True] + [False] * 8
    assert paired_mcnemar(a, b) == 1.0


def test_mcnemar_asymmetric_small_sample_p_value():
    """3 cells flip in favour of B, 1 in favour of A — known small p."""
    a = [True, False, False, False, False] + [True] * 5
    b = [False, True, True, True, True] + [True] * 5
    # n10=1, n01=4, n_disc=5, k=1
    # tail = C(5,0)*0.5^5 + C(5,1)*0.5^5 = (1 + 5)/32 = 0.1875
    # p = 2 * 0.1875 = 0.375
    p = paired_mcnemar(a, b)
    assert math.isclose(p, 0.375, rel_tol=1e-9)


def test_mcnemar_mismatched_lengths_raise():
    with pytest.raises(ValueError, match="equal-length"):
        paired_mcnemar([True, False], [True, False, True])


def test_mcnemar_empty_inputs_raise():
    with pytest.raises(ValueError, match="at least one"):
        paired_mcnemar([], [])


def test_mcnemar_p_value_in_unit_interval():
    """Sanity: across many shapes, p stays in [0, 1]."""
    cases = [
        ([True] * 5 + [False] * 5, [True] * 7 + [False] * 3),
        ([True] * 9 + [False], [False] + [True] * 9),
        ([False] * 10, [True, False, True, False, True, False, True, False, True, False]),
    ]
    for a, b in cases:
        p = paired_mcnemar(a, b)
        assert 0.0 <= p <= 1.0
