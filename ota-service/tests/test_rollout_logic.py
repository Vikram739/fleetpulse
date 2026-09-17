import random

from app.rollout_logic import (
    FAILED,
    SUCCESS,
    UNRESPONSIVE,
    compute_failure_rate,
    is_final_stage,
    select_new_batch_vehicle_ids,
    should_trigger_rollback,
    simulate_outcomes,
    target_batch_size,
)


def test_target_batch_size_rounds_up() -> None:
    assert target_batch_size(23, 10) == 3
    assert target_batch_size(20, 10) == 2
    assert target_batch_size(0, 10) == 0


def test_select_new_batch_vehicle_ids_first_stage() -> None:
    all_ids = [f"veh-{i}" for i in range(20)]
    selected = select_new_batch_vehicle_ids(all_ids, set(), 10)
    assert len(selected) == 2


def test_select_new_batch_vehicle_ids_excludes_already_assigned() -> None:
    all_ids = [f"veh-{i}" for i in range(20)]
    already = {"veh-0", "veh-1"}
    selected = select_new_batch_vehicle_ids(all_ids, already, 10)
    assert len(selected) == 0
    assert all(v not in already for v in selected)


def test_select_new_batch_vehicle_ids_second_stage_adds_delta() -> None:
    all_ids = [f"veh-{i}" for i in range(20)]
    already = {"veh-0", "veh-1"}
    selected = select_new_batch_vehicle_ids(all_ids, already, 50)
    assert len(selected) == 8
    assert all(v not in already for v in selected)


def test_select_new_batch_vehicle_ids_empty_fleet() -> None:
    selected = select_new_batch_vehicle_ids([], set(), 10)
    assert selected == []


def test_compute_failure_rate_empty_outcomes() -> None:
    assert compute_failure_rate({}) == 0.0


def test_compute_failure_rate_basic() -> None:
    outcomes = {"a": SUCCESS, "b": FAILED, "c": FAILED, "d": UNRESPONSIVE}
    assert compute_failure_rate(outcomes) == 0.5


def test_should_trigger_rollback_below_threshold() -> None:
    assert should_trigger_rollback(0.10, 15) is False


def test_should_trigger_rollback_above_threshold() -> None:
    assert should_trigger_rollback(0.20, 15) is True


def test_should_trigger_rollback_exactly_at_threshold_does_not_trigger() -> None:
    assert should_trigger_rollback(0.15, 15) is False


def test_simulate_outcomes_deterministic_with_seeded_rng() -> None:
    rng = random.Random(42)
    outcomes = simulate_outcomes(
        ["veh-1", "veh-2", "veh-3"],
        success_probability=0.5,
        failure_probability=0.3,
        unresponsive_probability=0.2,
        rng=rng,
    )
    assert set(outcomes.keys()) == {"veh-1", "veh-2", "veh-3"}
    assert all(v in {SUCCESS, FAILED, UNRESPONSIVE} for v in outcomes.values())


def test_simulate_outcomes_all_success_when_probability_is_one() -> None:
    outcomes = simulate_outcomes(
        ["veh-1", "veh-2"],
        success_probability=1.0,
        failure_probability=0.0,
        unresponsive_probability=0.0,
    )
    assert all(status == SUCCESS for status in outcomes.values())


def test_is_final_stage() -> None:
    stages = [10, 50, 100]
    assert is_final_stage(0, stages) is False
    assert is_final_stage(1, stages) is False
    assert is_final_stage(2, stages) is True
