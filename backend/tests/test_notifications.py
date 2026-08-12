from app.routes.notifications import _days_until, _item


def test_notification_item_has_expected_shape():
    item = _item("inventory-1", "inventory", "Inventory warning", "Review batch", "warning", "/inventory")
    assert item == {
        "id": "inventory-1",
        "category": "inventory",
        "title": "Inventory warning",
        "message": "Review batch",
        "severity": "warning",
        "action_url": "/inventory",
        "created_at": None,
    }


def test_invalid_collection_date_is_ignored():
    assert _days_until("not-a-date") is None
