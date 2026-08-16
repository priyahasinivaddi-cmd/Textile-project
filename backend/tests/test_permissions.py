from types import SimpleNamespace

from app.utils.permissions import can_access_batch


def test_unassigned_sustainability_officer_can_access_legacy_batch():
    officer = SimpleNamespace(role="manager", organization_id=None)
    legacy_batch = SimpleNamespace(owner=None)

    assert can_access_batch(officer, legacy_batch) is True


def test_manager_can_access_batches_across_organizations():
    officer = SimpleNamespace(role="manager", organization_id=7)
    legacy_batch = SimpleNamespace(owner=None)
    organization_batch = SimpleNamespace(owner=SimpleNamespace(organization_id=7))
    other_batch = SimpleNamespace(owner=SimpleNamespace(organization_id=9))

    assert can_access_batch(officer, legacy_batch) is True
    assert can_access_batch(officer, organization_batch) is True
    assert can_access_batch(officer, other_batch) is True


def test_manufacturer_can_access_every_batch():
    manufacturer = SimpleNamespace(role="manufacturer", id=21)
    legacy_batch = SimpleNamespace(owner_id=None)
    own_batch = SimpleNamespace(owner_id=21)
    other_batch = SimpleNamespace(owner_id=99)

    assert can_access_batch(manufacturer, legacy_batch) is True
    assert can_access_batch(manufacturer, own_batch) is True
    assert can_access_batch(manufacturer, other_batch) is True
