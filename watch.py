import os, re, requests

URL = "https://wohnservice-wien.at/aktuelles"
NTFY = os.environ["NTFY_URL"]            # --> kommt als Secret aus GitHub
SEEN_FILE = ".seen_cache/seen.txt"       # wird per Actions-Cache erhalten

def extract_links(html: str):
    # Alle Detail-Links der Aktuelles-Seite
    return sorted(set(re.findall(r'/aktuelles/aktuelles-detail/[^"\']+', html)))

def notify(title: str, body: str, url: str | None = None):
    headers = {"Title": title}
    if url:
        headers["Click"] = url
    requests.post(NTFY, data=body.encode("utf-8"), headers=headers, timeout=15)

def load_seen() -> set[str]:
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(l.strip() for l in f if l.strip())

def save_seen(links: set[str]):
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        f.write("\n".join(sorted(links)))

def main():
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
    r.raise_for_status()
    links = extract_links(r.text)
    if not links:
        return

    seen = load_seen()
    new_links = [l for l in links if l not in seen]

    if new_links:
        for rel in new_links:
            full = "https://wohnservice-wien.at" + rel
            # Optional: Titel holen
            title = "Neuer Beitrag"
            try:
                pr = requests.get(full, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
                m = re.search(r"<h1[^>]*>(.*?)</h1>", pr.text, flags=re.I|re.S)
                if m:
                    title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                else:
                    t = re.search(r"<title[^>]*>(.*?)</title>", pr.text, flags=re.I|re.S)
                    if t: title = re.sub(r"<[^>]+>", "", t.group(1)).strip()
            except Exception:
                pass
            notify("Wohnservice Wien", f"{title}\n{full}", full)

        # Liste aktualisieren und begrenzen
        seen.update(links)
        save_seen(set(list(seen)[:500]))

if __name__ == "__main__":
    main()
