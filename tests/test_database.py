from core import database


def _add(title, category="General", **kw):
    return database.add_password(title, "user", "cipher", category, **kw)


def test_crud(db):
    rid = _add("GitHub", "Work", url="https://github.com", notes="2FA on")
    row = database.get_password(rid)
    assert row["title"] == "GitHub" and row["url"] == "https://github.com"

    database.update_password(rid, "GitHub2", "u2", "c2", "Work", "", "")
    assert database.get_password(rid)["title"] == "GitHub2"

    database.delete_password(rid)
    assert database.get_password(rid) is None
    assert database.count_passwords() == 0


def test_filters_and_search(db):
    a = _add("Gmail", "Email", notes="personal")
    _add("Bank", "Banking")
    database.toggle_favorite(a)
    database.update_last_used(a)

    assert [r["title"] for r in database.get_all_passwords("Favorites")] == ["Gmail"]
    assert [r["title"] for r in database.get_all_passwords("Recent")] == ["Gmail"]
    assert [r["title"] for r in database.get_all_passwords("Banking")] == ["Bank"]
    assert database.get_all_passwords()[0]["title"] == "Gmail"  # favourites first
    assert [r["title"] for r in database.search_passwords("PERSONAL")] == ["Gmail"]
    assert database.get_categories() == ["Banking", "Email"]


def test_db_path_override(db):
    assert database.get_db_path() == str(db)
    assert db.exists()
