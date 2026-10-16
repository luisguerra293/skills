#!/usr/bin/env python3
"""Ferramentas para traduzir ficheiros .po (Loco Translate) para pt_PT.

Comandos:
  stats    <po>                      Resumo: total, traduzidas, em falta, fuzzy
  extract  <po> <out.json> [--chunk N --part K]
                                     Exporta strings em falta + fuzzy para JSON
  apply    <po> <translations.json> <out.po>
                                     Aplica traduções, limpa fuzzy nas revistas
  validate <po>                      Verifica placeholders, HTML, plurais, entidades

Formato do JSON de extração (lista):
  {"id": 12, "msgctxt": null, "msgid": "...", "msgid_plural": null,
   "fuzzy": false, "current": ["..."], "comment": "...", "occurrences": ["file:line"]}
Formato do JSON de traduções (lista):
  {"id": 12, "msgstr": "..."}  ou  {"id": 12, "msgstr": ["singular", "plural"]}
O "id" é o índice da entrada no ficheiro .po original (estável entre extract e apply).
"""
import json
import re
import sys

import polib

PLACEHOLDER_RE = re.compile(
    r"%(?:\d+\$)?[-+ 0#]*(?:\d+|\*)?(?:\.\d+)?[sdifuxXeEgGcoO%]"  # printf
    r"|\{\{?[^{}\s]+\}\}?"  # {name} / {{name}}
    r"|%[A-Za-z_][A-Za-z0-9_]*%"  # %name%
    r"|\[[a-z_]+[^\]]*\]"  # [shortcode]
    r"|\{[0-9]+\}"  # {0}
)
TAG_RE = re.compile(r"</?[A-Za-z][A-Za-z0-9]*(?:\s[^<>]*)?/?>")
ENTITY_RE = re.compile(r"&(?:[A-Za-z]+|#\d+|#x[0-9A-Fa-f]+);")


def load(path):
    po = polib.pofile(path, wrapwidth=0)
    return po


def entries_needing_work(po):
    for idx, e in enumerate(po):
        if e.obsolete:
            continue
        if "fuzzy" in e.flags:
            yield idx, e
        elif e.msgid_plural:
            if not all(v.strip() for v in e.msgstr_plural.values()):
                yield idx, e
        elif not e.msgstr.strip():
            yield idx, e


def cmd_stats(path):
    po = load(path)
    live = [e for e in po if not e.obsolete and e.msgid]
    fuzzy = [e for e in live if "fuzzy" in e.flags]
    missing = [
        e
        for e in live
        if "fuzzy" not in e.flags
        and (
            (e.msgid_plural and not all(v.strip() for v in e.msgstr_plural.values()))
            or (not e.msgid_plural and not e.msgstr.strip())
        )
    ]
    done = len(live) - len(fuzzy) - len(missing)
    print(f"Idioma: {po.metadata.get('Language')}")
    print(f"Plural-Forms: {po.metadata.get('Plural-Forms')}")
    print(f"Total: {len(live)} | Traduzidas: {done} | Fuzzy: {len(fuzzy)} | Em falta: {len(missing)}")


def cmd_extract(path, out, chunk=None, part=1):
    po = load(path)
    items = []
    for idx, e in entries_needing_work(po):
        if not e.msgid:
            continue
        current = (
            [e.msgstr_plural[k] for k in sorted(e.msgstr_plural)]
            if e.msgid_plural
            else [e.msgstr]
        )
        items.append(
            {
                "id": idx,
                "msgctxt": e.msgctxt,
                "msgid": e.msgid,
                "msgid_plural": e.msgid_plural or None,
                "fuzzy": "fuzzy" in e.flags,
                "current": current,
                "comment": e.comment or None,
                "occurrences": [f"{f}:{l}" for f, l in e.occurrences[:2]],
            }
        )
    total = len(items)
    if chunk:
        start = (part - 1) * chunk
        items = items[start : start + chunk]
        parts = -(-total // chunk)
        print(f"Parte {part}/{parts} ({len(items)} de {total} strings)")
    else:
        print(f"{total} strings para traduzir/rever")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)


def _check(msgid, msgstr):
    """Devolve lista de problemas entre original e tradução."""
    problems = []
    if not msgstr.strip():
        return problems
    for name, rx in (("placeholder", PLACEHOLDER_RE), ("tag HTML", TAG_RE), ("entidade", ENTITY_RE)):
        a = sorted(rx.findall(msgid))
        b = sorted(rx.findall(msgstr))
        if a != b:
            problems.append(f"{name}: original {a} != tradução {b}")
    if msgid.endswith("\n") != msgstr.endswith("\n"):
        problems.append("quebra de linha final diferente")
    if msgid.startswith(" ") != msgstr.startswith(" ") or msgid.endswith(" ") != msgstr.endswith(" "):
        problems.append("espaços no início/fim diferentes")
    return problems


def check_entry(e):
    problems = []
    if e.msgid_plural:
        for k, v in sorted(e.msgstr_plural.items()):
            src = e.msgid if k == 0 else e.msgid_plural
            problems += [f"[{k}] {p}" for p in _check(src, v)]
    else:
        problems = _check(e.msgid, e.msgstr)
    return problems


def cmd_apply(path, trans_path, out):
    po = load(path)
    with open(trans_path, encoding="utf-8") as f:
        trans = json.load(f)
    nplurals = int(re.search(r"nplurals\s*=\s*(\d+)", po.metadata.get("Plural-Forms", "nplurals=2")).group(1))
    applied = skipped = 0
    for t in trans:
        e = po[t["id"]]
        ms = t["msgstr"]
        if e.msgid_plural:
            if not isinstance(ms, list):
                print(f"AVISO id {t['id']}: plural exige lista, ignorado")
                skipped += 1
                continue
            for i in range(nplurals):
                e.msgstr_plural[i] = ms[min(i, len(ms) - 1)]
        else:
            if isinstance(ms, list):
                ms = ms[0]
            e.msgstr = ms
        if "fuzzy" in e.flags:
            e.flags.remove("fuzzy")
        e.previous_msgid = None
        e.previous_msgid_plural = None
        e.previous_msgctxt = None
        applied += 1
    po.save(out)
    print(f"Aplicadas: {applied} | Ignoradas: {skipped} -> {out}")


def cmd_validate(path):
    po = load(path)
    bad = 0
    for e in po:
        if e.obsolete or not e.msgid:
            continue
        for p in check_entry(e):
            bad += 1
            print(f"- {e.msgid[:80]!r}: {p}")
    cmd_stats(path)
    print("Problemas encontrados:", bad)
    return 1 if bad else 0


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "stats":
        cmd_stats(argv[2])
    elif cmd == "extract":
        chunk = part = None
        rest = argv[4:]
        if "--chunk" in rest:
            chunk = int(rest[rest.index("--chunk") + 1])
        part = int(rest[rest.index("--part") + 1]) if "--part" in rest else 1
        cmd_extract(argv[2], argv[3], chunk, part)
    elif cmd == "apply":
        cmd_apply(argv[2], argv[3], argv[4])
    elif cmd == "validate":
        return cmd_validate(argv[2])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
