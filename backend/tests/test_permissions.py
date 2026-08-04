from types import SimpleNamespace

from app.utils.permissions import can_access_batch


def test_unassigned_sustainability_officer_can_access_legacy_batch():
    officer = SimpleNamespace(role="manager", organization_id=None)
    legacy_batch = SimpleNamespace(owner=None)

    assert can_access_batch(officer, legacy_batch) is True


def test_organization_officer_can_access_legacy_and_organization_batches():
    officer = SimpleNamespace(role="manager", organization_id=7)
    legacy_batch = SimpleNamespace(owner=None)
    organization_batch = SimpleNamespace(owner=SimpleNamespace(organization_id=7))
    other_batch = SimpleNamespace(owner=SimpleNamespace(organization_id=9))

    assert can_access_batch(officer, legacy_batch) is True
    assert can_access_batch(officer, organization_batch) is True
    assert can_access_batch(officer, other_batch) is False
