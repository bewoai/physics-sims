"""Upload-Post ile tek istekte TikTok + Instagram Reels + YouTube Shorts.

API: POST https://api.upload-post.com/api/upload  (Authorization: Apikey <anahtar>)
Durum: GET /api/uploadposts/status?request_id=...
Sırlar ortam değişkeninden: UPLOAD_POST_API_KEY, UPLOAD_POST_USER (Upload-Post'taki profil adı).
Ücretsiz planda TikTok yok ve ayda 10 yükleme sınırı var → Basic plan gerekli.
"""
import os
import time

import requests

API = "https://api.upload-post.com/api"
PLATFORMS = ["tiktok", "instagram", "youtube"]


def configured():
    return bool(os.environ.get("UPLOAD_POST_API_KEY") and os.environ.get("UPLOAD_POST_USER"))


def upload(video, cap, request_id, platforms=PLATFORMS):
    key, user = os.environ["UPLOAD_POST_API_KEY"], os.environ["UPLOAD_POST_USER"]
    headers = {"Authorization": f"Apikey {key}", "Idempotency-Key": request_id}
    data = [("user", user), ("title", cap["youtube_title"]), ("async_upload", "true"), ("request_id", request_id),
            ("tiktok_title", cap["caption"]), ("privacy_level", "PUBLIC_TO_EVERYONE"),
            ("instagram_title", cap["caption"]), ("media_type", "REELS"), ("share_to_feed", "true"),
            ("youtube_title", cap["youtube_title"]), ("youtube_description", cap["youtube_description"]),
            ("privacyStatus", "public"), ("categoryId", "24")]
    data += [("platform[]", p) for p in platforms]
    data += [("tags[]", t) for t in cap["tags"]]
    with open(video, "rb") as fh:
        r = requests.post(f"{API}/upload", headers=headers, data=data,
                          files={"video": (os.path.basename(video), fh, "video/mp4")}, timeout=600)
    body = _json(r)
    if r.status_code >= 400:
        raise RuntimeError(f"Upload-Post {r.status_code}: {body}")
    return body


def wait(request_id, timeout=900, every=20):
    """Arka plandaki yüklemenin bitmesini bekler; platform sonuçlarını döndürür."""
    key = os.environ["UPLOAD_POST_API_KEY"]
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        r = requests.get(f"{API}/uploadposts/status", params={"request_id": request_id},
                         headers={"Authorization": f"Apikey {key}"}, timeout=60)
        last = _json(r)
        status = str(last.get("status", "")).lower()
        # durumlar: pending, queued, processing, in_progress, completed, failed, not_found
        # karışık sonuçta (biri başarılı biri değil) durum adı belgelenmemiş → completed >= total ile de bitir
        done = last.get("total") and (last.get("completed") or 0) >= last["total"]
        if status in ("completed", "failed", "not_found") or done:
            return last
        time.sleep(every)
    return {"status": "timeout", "last": last}


def _json(r):
    try:
        return r.json()
    except ValueError:
        return {"raw": r.text[:2000]}
