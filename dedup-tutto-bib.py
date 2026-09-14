#!/usr/bin/env python3
"""Conservative duplicate-entry merger for tutto.bib.

bibtex-tidy's --duplicates=citation does fuzzy title matching, which has
twice caused real damage here: it collapsed distinct works that merely
share a generic title (see commit 8518c2b), and separately its --escape
option corrupted crossref values containing "|" into "\\vert{}". This
script never touches formatting/escaping and only merges entries when
one of these narrow, unambiguous conditions holds:

  - two entries share the exact same citation key
  - two entries have the exact same DOI (normalized)
  - two entries share the same key "stem" (everything before the final
    ":<year>") and one uses a legacy 2-digit year where the other uses
    the matching full 4-digit year (e.g. foo:99 next to foo:1999)

Fuzzy title similarity is never used as a merge signal.

When entries are merged, the surviving entry is the one with the
full 4-digit-year key (falling back to the one with more fields, then
the one appearing first in the file); fields present only on the
discarded entry are appended to the survivor, and any crossref
elsewhere in the file pointing at a discarded key is repointed to the
survivor's key. All non-merged entries are left byte-for-byte
unchanged.

Usage:
  ./dedup-tutto-bib.py tutto.bib                  # dry run: report only
  ./dedup-tutto-bib.py tutto.bib --apply          # rewrite in place (keeps tutto.bib.bak)
  ./dedup-tutto-bib.py tutto.bib --apply -o out.bib   # write elsewhere instead
"""

import argparse
import re
import sys
from dataclasses import dataclass, field


@dataclass
class Entry:
    etype: str
    key: str
    start: int
    end: int
    raw_text: str
    fields: list  # list of (name, value) in original order, value includes braces if any

    def field_map(self):
        return {name.lower(): value for name, value in self.fields}


ENTRY_START_RE = re.compile(r"(?m)^@")
HEADER_RE = re.compile(r"@(?P<type>[A-Za-z]+)\{(?P<key>[^,\s]+),")


def split_entries(text):
    """Split the raw .bib text into a list of Entry objects, brace-depth aware."""
    starts = [m.start() for m in ENTRY_START_RE.finditer(text)]
    entries = []
    for idx, s in enumerate(starts):
        brace_open = text.index("{", s)
        depth = 0
        j = brace_open
        n = len(text)
        while j < n:
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        else:
            raise ValueError(f"Unbalanced braces starting at offset {s}")
        # include one trailing newline in the entry's span, so entries
        # concatenate back to the original file with no separate "gap" text
        if j < n and text[j] == "\n":
            j += 1
        end = j

        raw = text[s:end]
        header = HEADER_RE.match(raw)
        if not header:
            raise ValueError(f"Could not parse entry header at offset {s}: {raw[:60]!r}")
        etype = header.group("type")
        key = header.group("key")
        body = raw[header.end():]
        fields = parse_fields(body)
        entries.append(Entry(etype, key, s, end, raw, fields))
    return entries


def parse_fields(body):
    """Parse 'name = value,' pairs from an entry body (after the key), brace-depth aware."""
    fields = []
    i, n = 0, len(body)
    while i < n:
        while i < n and body[i] in " \t\r\n,":
            i += 1
        if i >= n:
            break
        # a lone trailing '}' (the entry's own closer) may remain if malformed; stop on it
        if body[i] == "}":
            break
        name_start = i
        while i < n and body[i] not in "=\n":
            i += 1
        if i >= n or body[i] != "=":
            break
        name = body[name_start:i].strip()
        i += 1
        while i < n and body[i] in " \t":
            i += 1
        if i < n and body[i] == "{":
            depth = 0
            val_start = i
            while i < n:
                if body[i] == "{":
                    depth += 1
                elif body[i] == "}":
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                i += 1
            value = body[val_start:i]
        else:
            val_start = i
            while i < n and body[i] not in ",\n":
                i += 1
            value = body[val_start:i].rstrip()
        fields.append((name, value))
    return fields


def strip_braces(value):
    value = value.strip()
    if value.startswith("{") and value.endswith("}"):
        return value[1:-1]
    return value


def normalize_doi(value):
    doi = strip_braces(value).strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi.rstrip("/")


def key_stem_year(key):
    if ":" not in key:
        return key, None
    stem, year = key.rsplit(":", 1)
    return stem, year


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def find_merge_groups(entries):
    uf = UnionFind(len(entries))

    by_key = {}
    for i, e in enumerate(entries):
        by_key.setdefault(e.key, []).append(i)
    for idxs in by_key.values():
        for i in idxs[1:]:
            uf.union(idxs[0], i)

    by_doi = {}
    for i, e in enumerate(entries):
        doi = e.field_map().get("doi")
        if doi:
            norm = normalize_doi(doi)
            if norm:
                by_doi.setdefault(norm, []).append(i)
    for idxs in by_doi.values():
        if len(idxs) > 1:
            for i in idxs[1:]:
                uf.union(idxs[0], i)

    by_stem = {}
    for i, e in enumerate(entries):
        stem, year = key_stem_year(e.key)
        if year is not None:
            by_stem.setdefault(stem, []).append((i, year))
    for idxs in by_stem.values():
        if len(idxs) < 2:
            continue
        for a in range(len(idxs)):
            i, yi = idxs[a]
            for b in range(a + 1, len(idxs)):
                j, yj = idxs[b]
                if legacy_year_match(yi, yj):
                    uf.union(i, j)

    groups = {}
    for i in range(len(entries)):
        groups.setdefault(uf.find(i), []).append(i)
    return [sorted(g) for g in groups.values() if len(g) > 1]


def legacy_year_match(y1, y2):
    if y1 == y2:
        return False  # identical stem+year means identical key, already handled by key match
    if not (y1.isdigit() and y2.isdigit()):
        return False
    short, full = (y1, y2) if len(y1) < len(y2) else (y2, y1)
    if len(short) != 2 or len(full) != 4:
        return False
    return int(full) % 100 == int(short)


def choose_survivor(entries, group):
    def rank(i):
        e = entries[i]
        _, year = key_stem_year(e.key)
        full_year = 1 if (year and len(year) == 4) else 0
        return (full_year, len(e.fields), -e.start)

    return max(group, key=rank)


FIELD_LINE_RE = re.compile(r"^\s*[A-Za-z0-9_.\-]+\s*=", re.MULTILINE)


def append_field(raw_text, name, value):
    close = raw_text.rstrip().rfind("}")
    line = f"  {name:<14}= {value},\n"
    return raw_text[:close] + line + raw_text[close:]


def merge_entries(entries):
    groups = find_merge_groups(entries)
    key_map = {}
    removed = set()
    report = []

    for group in groups:
        survivor_idx = choose_survivor(entries, group)
        survivor = entries[survivor_idx]
        present = {name.lower() for name, _ in survivor.fields}
        merged_from = []
        for i in group:
            if i == survivor_idx:
                continue
            other = entries[i]
            key_map[other.key] = survivor.key
            removed.add(i)
            merged_from.append(other.key)
            for name, value in other.fields:
                if name.lower() not in present:
                    survivor.raw_text = append_field(survivor.raw_text, name, value)
                    present.add(name.lower())
        report.append((survivor.key, merged_from))

    # resolve chains (A -> B, B -> C  =>  A -> C) just in case
    def resolve(k):
        seen = set()
        while k in key_map and k not in seen:
            seen.add(k)
            k = key_map[k]
        return k

    key_map = {k: resolve(v) for k, v in key_map.items()}

    # repoint crossrefs anywhere in the (surviving) bibliography
    crossref_re_cache = {}
    for i, e in enumerate(entries):
        if i in removed:
            continue
        for name, value in e.fields:
            if name.lower() != "crossref":
                continue
            ref = strip_braces(value)
            if ref in key_map:
                new_ref = key_map[ref]
                pattern = crossref_re_cache.get(ref)
                if pattern is None:
                    pattern = re.compile(
                        r"(crossref\s*=\s*\{)" + re.escape(ref) + r"(\})",
                        re.IGNORECASE,
                    )
                    crossref_re_cache[ref] = pattern
                e.raw_text = pattern.sub(lambda m: m.group(1) + new_ref + m.group(2), e.raw_text)

    kept = [e for i, e in enumerate(entries) if i not in removed]
    return kept, report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("bibfile", help="path to the .bib file to dedup")
    parser.add_argument("--apply", action="store_true", help="write the merged result (default is dry-run report only)")
    parser.add_argument("-o", "--output", help="write to this path instead of overwriting bibfile (implies --apply)")
    args = parser.parse_args()

    with open(args.bibfile, encoding="utf-8") as f:
        text = f.read()

    entries = split_entries(text)
    kept, report = merge_entries(entries)

    if not report:
        print("No merge candidates found.")
        return

    print(f"{len(report)} merge group(s) found:")
    for survivor_key, merged_from in report:
        for old_key in merged_from:
            print(f"  {old_key}  ->  {survivor_key}")

    if not (args.apply or args.output):
        print("\nDry run only. Re-run with --apply to write changes.")
        return

    out_path = args.output or args.bibfile
    new_text = "".join(e.raw_text for e in kept)

    if not args.output:
        backup_path = args.bibfile + ".bak"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\nBacked up original to {backup_path}")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(new_text)
    print(f"Wrote {out_path} ({len(kept)} entries, was {len(entries)}).")


if __name__ == "__main__":
    main()
