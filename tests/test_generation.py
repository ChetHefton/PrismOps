"""Tests for deterministic synthetic ticket generation."""

from pathlib import Path

from scripts.generate_support_demo import SEED, generate_tickets, write_tickets


def test_synthetic_generation_is_reproducible() -> None:
    first = generate_tickets(count=100, seed=SEED)
    second = generate_tickets(count=100, seed=SEED)
    different = generate_tickets(count=100, seed=SEED + 1)

    assert first == second
    assert first != different
    assert len({ticket["ticket_id"] for ticket in first}) == 100


def test_committed_dataset_matches_generator(tmp_path: Path) -> None:
    regenerated = tmp_path / "support_tickets.csv"
    write_tickets(regenerated, generate_tickets())

    assert regenerated.read_bytes() == Path("data/demo/support_tickets.csv").read_bytes()
