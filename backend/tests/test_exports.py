from tests.helpers import register_and_login


def test_export_report_pdf(client):
    _, headers = register_and_login(client, 9)

    create = client.post(
        "/exports/report",
        headers=headers,
        json={"period_start": "2026-02-01", "period_end": "2026-02-15"},
    )
    assert create.status_code == 200
    report_id = create.json()["report_id"]

    status = client.get(f"/exports/report/{report_id}", headers=headers)
    assert status.status_code == 200
    assert status.json()["status"] in {"ready", "processing"}

    if status.json()["status"] == "ready":
        download = client.get(f"/exports/report/{report_id}/download", headers=headers)
        assert download.status_code == 200
        assert download.headers["content-type"] == "application/pdf"

