from tests.helpers import register_and_login


def test_my_dashboard_profile_and_trails(client):
    _, headers = register_and_login(client, 9)

    profile = client.get("/me/profile", headers=headers)
    assert profile.status_code == 200
    assert "xp" in profile.json()
    assert "mascot" in profile.json()

    dashboard = client.get("/me/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert "headline" in dashboard.json()
    assert "recent_xp" in dashboard.json()

    trails = client.get("/me/trails", headers=headers)
    assert trails.status_code == 200
    items = trails.json()["items"]
    assert items
    generated = [item for item in items if item.get("is_generated")]
    bundle_signatures = {tuple(sorted(item.get("lesson_ids") or [])) for item in generated if item.get("lesson_ids")}
    assert len(bundle_signatures) == len([item for item in generated if item.get("lesson_ids")])
