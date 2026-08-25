from types import SimpleNamespace
from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.http_policy import application_release


def test_json_gets_release_scoped_validator_and_safe_post_validation_304(monkeypatch) -> None:
    release = SimpleNamespace(release_id="serve-test-a")
    app_release = SimpleNamespace(value="app-test-a")
    monkeypatch.setattr(main, "release_store", lambda: release)
    monkeypatch.setattr(main, "application_release", lambda: app_release.value)
    client = TestClient(main.create_app())

    first = client.get("/api/v1/search", params={"q": "P00533"})
    assert first.status_code == 200
    assert first.headers["cache-control"] == "public, max-age=0, must-revalidate"
    assert first.headers["x-memvar-release"] == "serve-test-a"
    assert first.headers["etag"].startswith('"')
    assert "P00533" not in first.headers["etag"]
    assert 'desc="/api/v1/search"' in first.headers["server-timing"]
    assert "P00533" not in first.headers["server-timing"]

    protein = client.get("/api/v1/proteins/P00533")
    assert protein.status_code == 200
    assert 'desc="/api/v1/proteins/{acc}"' in protein.headers["server-timing"]
    assert "P00533" not in protein.headers["server-timing"]

    revalidated = client.get(
        "/api/v1/search", params={"q": "P00533"},
        headers={"If-None-Match": first.headers["etag"]},
    )
    assert revalidated.status_code == 304
    assert revalidated.content == b""
    assert "content-length" not in revalidated.headers
    assert revalidated.headers["etag"] == first.headers["etag"]

    release.release_id = "serve-test-b"
    changed_release = client.get(
        "/api/v1/search", params={"q": "P00533"},
        headers={"If-None-Match": first.headers["etag"]},
    )
    assert changed_release.status_code == 200
    assert changed_release.headers["x-memvar-release"] == "serve-test-b"
    assert changed_release.headers["etag"] != first.headers["etag"]

    release.release_id = "serve-test-a"
    app_release.value = "app-test-b"
    changed_app_release = client.get(
        "/api/v1/search", params={"q": "P00533"},
        headers={"If-None-Match": first.headers["etag"]},
    )
    assert changed_app_release.status_code == 200
    assert changed_app_release.headers["etag"] != first.headers["etag"]


def test_errors_are_never_short_circuited_by_a_conditional_request(monkeypatch) -> None:
    monkeypatch.setattr(main, "release_store", lambda: SimpleNamespace(release_id="serve-test"))
    monkeypatch.setattr(main, "application_release", lambda: "app-test")
    client = TestClient(main.create_app())

    missing = client.get(
        "/api/v1/proteins/NOT_A_PROTEIN",
        headers={"If-None-Match": "*"},
    )
    assert missing.status_code == 404
    assert missing.headers["cache-control"] == "no-store"
    assert "etag" not in missing.headers


def test_json_is_not_cached_without_a_reliable_application_release(monkeypatch) -> None:
    monkeypatch.setattr(main, "release_store", lambda: SimpleNamespace(release_id="serve-test"))
    monkeypatch.setattr(main, "application_release", lambda: None)
    response = TestClient(main.create_app()).get("/api/v1/search", params={"q": "P00533"})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "etag" not in response.headers


def test_application_release_requires_an_explicit_nonempty_identity(monkeypatch) -> None:
    monkeypatch.delenv("MEMVAR_APP_RELEASE", raising=False)
    assert application_release() is None
    monkeypatch.setenv("MEMVAR_APP_RELEASE", "  app-release  ")
    assert application_release() == "app-release"


def test_start_local_uses_a_startup_fixed_dirty_identity_without_blocking_startup() -> None:
    script = (Path(__file__).resolve().parents[2] / "start-local.sh").read_text(encoding="utf-8")
    assert 'git -C "$website_dir" status --porcelain --untracked-files=all' in script
    assert 'MEMVAR_APP_RELEASE="$app_git_head"' in script
    assert 'app_identity_nonce="$(date +%s%N)-$$"' in script
    assert 'MEMVAR_APP_RELEASE="${app_git_head}-dirty-${app_identity_nonce}"' in script
    assert '[[ -z "${MEMVAR_APP_RELEASE:-}" ]] || export MEMVAR_APP_RELEASE' in script
