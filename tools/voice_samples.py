#!/usr/bin/env python3
"""Render a short sample of the newest episode in every Chirp 3 HD voice.

Usage: voice_samples.py OUT_DIR   (needs GOOGLE_TTS_API_KEY)
Writes OUT_DIR/<voice>.mp3 and OUT_DIR/index.html, a page to audition them.
"""
import base64, glob, html, json, os, sys, urllib.request

KEY = os.environ["GOOGLE_TTS_API_KEY"]
API = "https://texttospeech.googleapis.com/v1"
LOCALES = {"en-US": "American", "en-GB": "British", "en-AU": "Australian"}

def call(path, body=None):
    req = urllib.request.Request(f"{API}/{path}",
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json", "X-Goog-Api-Key": KEY})
    return json.load(urllib.request.urlopen(req, timeout=120))

def sample_text():
    newest = sorted(glob.glob("episodes/*.txt"))[-1]
    paras = [p.strip() for p in open(newest).read().split("\n\n") if p.strip()]
    text = ""
    for p in paras:
        if len(text) > 350: break
        text = (text + "\n\n" + p).strip()
    return text[:900]

def main(out):
    os.makedirs(out, exist_ok=True)
    text, rate = sample_text(), float(os.environ.get("GOOGLE_TTS_RATE") or 1.05)
    current = os.environ.get("GOOGLE_TTS_VOICE") or "en-US-Chirp3-HD-Aoede"
    rows = []
    for loc, label in LOCALES.items():
        voices = sorted((v for v in call(f"voices?languageCode={loc}")["voices"]
                         if "Chirp3-HD" in v["name"] and loc in v["languageCodes"]), key=lambda v: v["name"])
        for v in voices:
            name = v["name"]
            try:
                audio = call("text:synthesize", {"input": {"text": text}, "voice": {"languageCode": loc, "name": name},
                                                 "audioConfig": {"audioEncoding": "MP3", "speakingRate": rate}})["audioContent"]
            except Exception as e:
                print(f"skip {name}: {e}", file=sys.stderr); continue
            open(os.path.join(out, f"{name}.mp3"), "wb").write(base64.b64decode(audio))
            rows.append((label, name, v.get("ssmlGender", "").title()))
            print("ok", name)
    body = []
    for label in LOCALES.values():
        items = [r for r in rows if r[0] == label]
        if not items: continue
        body.append(f"<h2>{label} English</h2>")
        for _, name, g in items:
            short = name.split("-")[-1]
            tag = " <b>(current)</b>" if name == current else ""
            body.append(f'<div class="v"><div><b>{html.escape(short)}</b> · {g}{tag}<br><code>{name}</code></div>'
                        f'<audio controls preload="none" src="{name}.mp3"></audio></div>')
    open(os.path.join(out, "index.html"), "w").write(f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>Briefing voices</title><style>
body{{font:16px -apple-system,system-ui,sans-serif;margin:0 auto;max-width:640px;padding:16px;background:#fff;color:#111}}
@media (prefers-color-scheme:dark){{body{{background:#111;color:#eee}}}}
.v{{padding:10px 0;border-bottom:1px solid #8884}} audio{{width:100%;margin-top:6px}} code{{font-size:12px;opacity:.7}}
</style></head><body><h1>Briefing voices</h1>
<p>Same opening paragraph in each Google Chirp 3 HD voice, at speed {rate}. Tell Claude the name you like.</p>
{''.join(body)}</body></html>""")
    print(f"{len(rows)} samples")

if __name__ == "__main__":
    main(sys.argv[1])
