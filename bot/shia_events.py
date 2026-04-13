import html
import re
import time
import xml.etree.ElementTree as ET

import requests
import settings as config

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    if not text:
        return ""
    clean = html.unescape(_TAG_RE.sub(" ", text))
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def _lc(value: str) -> str:
    return (value or "").strip().lower()


class ShiaEventsFeed:
    def __init__(self):
        self.enabled = bool(
            config.ENABLE_SHIA_EVENTS_FEED and config.SHIA_EVENTS_FEED_URLS
        )
        self.feed_urls = list(config.SHIA_EVENTS_FEED_URLS)
        self.keywords = [_lc(word) for word in config.SHIA_EVENTS_KEYWORDS]
        self.max_items_per_poll = int(config.SHIA_EVENTS_MAX_ITEMS_PER_POLL)
        self.poll_seconds = int(config.SHIA_EVENTS_POLL_SECONDS)
        self.next_poll_at = 0.0
        self._seen_ids: set[str] = set()
        self._seen_order: list[str] = []
        self._max_seen = 1000

    def should_poll(self) -> bool:
        return self.enabled and time.time() >= self.next_poll_at

    def mark_polled(self) -> None:
        self.next_poll_at = time.time() + self.poll_seconds

    def _remember(self, key: str) -> None:
        if not key or key in self._seen_ids:
            return
        self._seen_ids.add(key)
        self._seen_order.append(key)
        while len(self._seen_order) > self._max_seen:
            old = self._seen_order.pop(0)
            self._seen_ids.discard(old)

    def _interesting(self, text: str) -> bool:
        subject = _lc(text)
        if not subject:
            return False
        return any(word in subject for word in self.keywords)

    def _parse_feed(self, raw_xml: str) -> list[dict]:
        root = ET.fromstring(raw_xml)
        entries: list[dict] = []

        channel = root.find("channel")
        if channel is not None:
            items = channel.findall("item")
            for item in items:
                title = _strip_html((item.findtext("title") or "").strip())
                link = (item.findtext("link") or "").strip()
                guid = (item.findtext("guid") or "").strip()
                desc = _strip_html(item.findtext("description") or "")
                key = guid or link or title
                entries.append(
                    {
                        "title": title,
                        "link": link,
                        "summary": desc,
                        "key": key,
                    }
                )
            return entries

        atom_ns = "{http://www.w3.org/2005/Atom}"
        atom_entries = root.findall(f"{atom_ns}entry")
        for entry in atom_entries:
            title = _strip_html((entry.findtext(f"{atom_ns}title") or "").strip())
            link = ""
            link_node = entry.find(f"{atom_ns}link")
            if link_node is not None:
                link = (link_node.attrib.get("href") or "").strip()
            guid = (entry.findtext(f"{atom_ns}id") or "").strip()
            summary = _strip_html(entry.findtext(f"{atom_ns}summary") or "")
            key = guid or link or title
            entries.append(
                {
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "key": key,
                }
            )
        return entries

    def get_updates(self) -> list[dict]:
        if not self.enabled:
            return []

        updates: list[dict] = []
        for url in self.feed_urls:
            if len(updates) >= self.max_items_per_poll:
                break
            try:
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                entries = self._parse_feed(response.text)
            except Exception as exc:
                print(f"  [Events] feed error: {url} -> {exc}")
                continue

            for entry in entries:
                if len(updates) >= self.max_items_per_poll:
                    break
                key = entry.get("key", "")
                title = entry.get("title", "")
                full_text = f"{title} {entry.get('summary', '')}".strip()
                if not key or key in self._seen_ids:
                    continue
                self._remember(key)
                if not self._interesting(full_text):
                    continue
                updates.append(entry)

        return updates
