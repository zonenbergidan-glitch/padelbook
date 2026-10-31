import pytest

from demo_weather import main


@pytest.mark.parametrize(
    "policy, assessment, requires_review, alternatives",
    [
        ("normal", "not_required", "False", "[]"),
        ("strict", "review_required", "True", "[2]"),
    ],
)
def test_selected_policy_changes_business_result(
    capsys, monkeypatch, policy, assessment, requires_review, alternatives
):
    def unexpected_network_call(*args, **kwargs):
        pytest.fail("Offline demonstration must not access the network")

    monkeypatch.setattr(
        "padelbook.weather_client.requests.get",
        unexpected_network_call,
    )

    main(["--policy", policy, "--demo-rain-mm", "0.75"])
    output = capsys.readouterr().out

    assert "Source: Synthetic offline data" in output
    assert f"Weather policy: {policy}" in output
    assert f"Weather assessment: {assessment}" in output
    assert f"Requires review: {requires_review}" in output
    assert f"Indoor alternatives: {alternatives}" in output
    assert "Original court: 1" in output
    assert "Booking status: confirmed" in output
    assert "Stored bookings: 1" in output
