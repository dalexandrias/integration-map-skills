#!/usr/bin/env python3
"""
Monta o mapa de integração a partir dos integrations.json espalhados pelos repositórios clonados.

Uso:
    python build_graph.py ~/repos
    python build_graph.py ~/repos --out ~/integration-map
    python build_graph.py ~/repos --check          # só valida, não escreve
    python build_graph.py ~/repos --aliases ~/integration-map/aliases.yml

Procura por  <raiz>/*/docs/architecture/integrations.json  (um nível de profundidade por
padrão; use --depth para procurar mais fundo).

Saída em --out (padrão: ./integration-map):
    graph.json   dados consolidados
    map.html     visualizador com os dados embutidos

Só depende da biblioteca padrão. pyyaml é opcional e só para o aliases.yml.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

LANES = {
    "frontend": 0, "job": 0, "app": 1, "topic": 2, "queue": 2,
    "database": 3, "cache": 3, "external-api": 4, "file": 4,
}
RELATIONS = {"publishes", "consumes", "calls", "reads", "writes",
             "schedules", "sends-file", "reads-file"}
# relações declaradas do ponto de vista da aplicação que precisam ser invertidas
# para a seta apontar no sentido do fluxo de dados
INVERT = {"consumes", "reads-file"}
LEVELS = {"high", "medium", "low"}
RANK = {"high": 3, "medium": 2, "low": 1}

PREFIX_TYPE = {
    "topic": "topic", "queue": "queue", "db": "database", "database": "database",
    "cache": "cache", "api": "external-api", "file": "file", "app": "app",
    "svc": "app", "job": "job", "front": "frontend",
}


def infer_type(node_id: str) -> str:
    return PREFIX_TYPE.get(node_id.split(".", 1)[0], "app")


def load_aliases(path: Path | None, warn: list[str]) -> dict[str, str]:
    """Mapa alias -> id canônico. Resolve o mesmo sistema citado com nomes diferentes."""
    if not path or not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    data = None
    try:
        import yaml
        data = yaml.safe_load(text)
    except ImportError:
        # fallback sem pyyaml: formato "canonico: [a, b]" ou "canonico: a"
        data = {}
        for line in text.splitlines():
            line = line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            k, v = line.split(":", 1)
            items = [x.strip().strip("'\"") for x in v.strip().strip("[]").split(",")]
            data[k.strip()] = [i for i in items if i]
    out: dict[str, str] = {}
    for canonical, aliases in (data or {}).items():
        if isinstance(aliases, str):
            aliases = [aliases]
        for a in aliases or []:
            if a in out and out[a] != canonical:
                warn.append(f"aliases: '{a}' aponta para '{out[a]}' e para '{canonical}'")
            out[a] = canonical
    return out


def find_scans(root: Path, depth: int) -> list[Path]:
    pattern = "/".join(["*"] * depth) + "/docs/architecture/integrations.json"
    return sorted(root.glob(pattern)) + sorted(root.glob("docs/architecture/integrations.json"))


def build(root: Path, out_dir: Path, aliases_path: Path | None, depth: int,
          auto_merge: bool = True):
    warn: list[str] = []
    alias = load_aliases(aliases_path, warn)
    canon = lambda i: alias.get(i, i)

    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    referenced: set[str] = set()
    seen_names: dict[str, str] = {}

    scans = find_scans(root, depth)
    if not scans:
        warn.append(f"nenhum integrations.json encontrado em {root} (profundidade {depth})")

    for scan in scans:
        repo_dir = scan.parent.parent.parent
        try:
            data = json.loads(scan.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            warn.append(f"{scan}: JSON inválido ({e.msg} linha {e.lineno}) — ignorado")
            continue

        app = data.get("app") or {}
        raw_id = app.get("id")
        if not raw_id:
            warn.append(f"{scan}: bloco 'app' sem 'id' — ignorado")
            continue
        app_id = canon(raw_id)

        atype = app.get("type", "app")
        if atype not in LANES:
            warn.append(f"{app_id}: tipo '{atype}' desconhecido, tratado como 'app'")
            atype = "app"

        # ficha markdown ao lado do scan, se existir
        doc = None
        for cand in (scan.parent / f"{raw_id}.md", scan.parent / f"{app_id}.md"):
            if cand.is_file():
                try:
                    doc = str(cand.resolve().relative_to(out_dir.resolve(), walk_up=True))
                except (ValueError, TypeError):
                    import os
                    doc = os.path.relpath(cand.resolve(), out_dir.resolve())
                break
        if doc is None:
            warn.append(f"{app_id}: sem ficha markdown (rode document-application)")

        name = app.get("name", app_id)
        if name in seen_names and seen_names[name] != app_id:
            warn.append(f"nome '{name}' usado por '{seen_names[name]}' e '{app_id}' — "
                        f"considere um alias")
        seen_names[name] = app_id

        if app_id in nodes and nodes[app_id].get("doc") is not None:
            warn.append(f"id '{app_id}' aparece em mais de um repositório — o último venceu")

        nodes[app_id] = {
            "id": app_id, "name": name, "type": atype,
            "subtype": app.get("subtype"), "repo": app.get("repo"),
            "owner": app.get("owner"), "criticality": app.get("criticality", "medium"),
            "tech": app.get("tech") or [], "envs": app.get("envs") or [],
            "detail": app.get("detail"), "doc": doc,
            "exposes": data.get("exposes") or [],
            "scanned_at": app.get("scanned_at"),
            "_dir": repo_dir.name,
        }

        for item in data.get("integrations") or []:
            target_raw = item.get("target")
            relation = item.get("relation")
            if not target_raw or not relation:
                warn.append(f"{app_id}: integração sem 'target' ou 'relation' — ignorada")
                continue
            target = canon(target_raw)
            if relation not in RELATIONS:
                warn.append(f"{app_id} → {target}: relação '{relation}' não é válida")
            conf = item.get("confidence", "high")
            if conf not in LEVELS:
                warn.append(f"{app_id} → {target}: confiança '{conf}' inválida")
                conf = "high"
            if not item.get("evidence"):
                warn.append(f"{app_id} → {target}: sem evidência (arquivo:linha)")

            referenced.add(target)
            # nó alvo descrito pela própria integração; a primeira descrição vence
            if target not in nodes:
                ttype = item.get("target_type") or infer_type(target)
                if ttype not in LANES:
                    warn.append(f"{target}: target_type '{ttype}' desconhecido")
                    ttype = infer_type(target)
                nodes[target] = {
                    "id": target, "name": item.get("target_name") or target.split(".", 1)[-1],
                    "type": ttype, "detail": item.get("target_detail"),
                    "criticality": item.get("criticality", "medium"),
                    "owner": item.get("target_owner"), "doc": None, "_stub": True,
                }
            elif nodes[target].get("_stub") and item.get("target_detail") and not nodes[target].get("detail"):
                nodes[target]["detail"] = item["target_detail"]

            src, dst = (target, app_id) if relation in INVERT else (app_id, target)
            edges.append({
                "from": src, "to": dst, "relation": relation,
                "protocol": item.get("protocol"), "contract": item.get("contract"),
                "criticality": item.get("criticality", "medium"),
                "timeout": item.get("timeout"), "retry": item.get("retry"),
                "evidence": item.get("evidence"), "confidence": conf,
                "note": item.get("note"),
            })

        for u in data.get("unresolved") or []:
            warn.append(f"{app_id}: não resolvido — {u.get('hint','?')} "
                        f"({u.get('where','?')}): {u.get('why','')}".strip())

    # ── Reconciliação de host × aplicação ────────────────────────────────
    # Um scan que só viu "http://svc-cotacao.interno:8080" grava api.svc-cotacao.interno,
    # enquanto o repositório svc-cotacao gera o nó svc-cotacao. Sem fundir os dois, o mapa
    # afirma que ninguém chama a aplicação — o erro mais caro que este script pode cometer,
    # porque é silencioso e parece certo.
    app_ids = {n["id"] for n in nodes.values()
               if not n.get("_stub") and n["type"] in ("app", "frontend", "job")}
    merges: dict[str, str] = {}
    for nid, n in list(nodes.items()):
        if not (n.get("_stub") and nid.startswith("api.")):
            continue
        host = nid[4:]
        if "." not in host:          # api.parceiro → nome de sistema, não hostname
            continue
        label = host.split(".")[0]
        if label in app_ids:
            if auto_merge:
                merges[nid] = label
            else:
                warn.append(f"'{nid}' é a aplicação '{label}' vista pelo hostname "
                            f"(fusão desligada por --no-auto-merge)")
        else:
            warn.append(f"'{nid}' tem cara de aplicação interna ainda não escaneada — "
                        f"candidato: '{label}'. Escaneie esse repositório ou registre "
                        f"um alias.")
    for old, new in merges.items():
        nodes.pop(old, None)
        warn.append(f"fundido: '{old}' → '{new}' (hostname bate com id de aplicação)")
    if merges:
        for e in edges:
            e["from"] = merges.get(e["from"], e["from"])
            e["to"] = merges.get(e["to"], e["to"])

    # Criticidade de nó compartilhado vem do maior valor entre as integrações que chegam
    # nele: um schema lido por três aplicações críticas é crítico, mesmo que a primeira
    # aresta encontrada fosse baixa. Sem isso o filtro de criticidade do mapa mente.
    incident: dict[str, str] = {}
    for e in edges:
        for side in (e["from"], e["to"]):
            cur = incident.get(side, "low")
            if RANK.get(e.get("criticality", "medium"), 2) > RANK.get(cur, 1):
                incident[side] = e.get("criticality", "medium")
    for n in nodes.values():
        if n.get("_stub") and n["id"] in incident:
            n["criticality"] = incident[n["id"]]

    # Aplicação citada por outra mas nunca escaneada: é a fila de trabalho do próximo
    # ciclo, e o motivo mais comum de um mapa parecer completo sem estar.
    for n in nodes.values():
        if n.get("_stub") and n["type"] in ("app", "frontend", "job"):
            warn.append(f"'{n['id']}' é citada como aplicação mas nunca foi escaneada — "
                        f"rode scan-integrations no repositório dela")

    # nós sem nenhuma aresta
    used = {e["from"] for e in edges} | {e["to"] for e in edges}
    for n in nodes.values():
        if n["id"] not in used:
            warn.append(f"'{n['id']}' não tem nenhuma integração ligada a ele")

    # arestas duplicadas exatas
    seen = set()
    for e in edges:
        k = (e["from"], e["to"], e["relation"], e.get("contract"))
        if k in seen:
            warn.append(f"integração duplicada: {e['from']} → {e['to']} ({e['relation']})")
        seen.add(k)

    for n in nodes.values():
        n.pop("_stub", None)
        n.pop("_dir", None)

    graph = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source_root": str(root),
        "nodes": sorted(nodes.values(), key=lambda n: (LANES.get(n["type"], 9), n["name"].lower())),
        "edges": edges,
        "warnings": warn,
    }
    return graph, len(scans)


def inject(template: Path, dest: Path, graph: dict) -> None:
    html = template.read_text(encoding="utf-8")
    payload = json.dumps(graph, ensure_ascii=False, indent=1)
    new, n = re.subn(
        r'(<script type="application/json" id="graph">)(.*?)(</script>)',
        lambda m: m.group(1) + "\n" + payload + "\n" + m.group(3),
        html, count=1, flags=re.S)
    if not n:
        sys.exit(f'não encontrei o bloco <script id="graph"> em {template}')
    dest.write_text(new, encoding="utf-8")


def summarize(graph: dict, scans: int) -> None:
    nodes, edges = graph["nodes"], graph["edges"]
    apps = [n for n in nodes if n["type"] in ("app", "frontend", "job")]
    print(f"repositórios lidos: {scans}")
    print(f"aplicações: {len(apps)}   nós totais: {len(nodes)}   integrações: {len(edges)}")
    by_proto = defaultdict(int)
    for e in edges:
        by_proto[e.get("protocol") or "?"] += 1
    if by_proto:
        print("por protocolo: " + "  ".join(f"{k}={v}" for k, v in sorted(by_proto.items())))
    low = [e for e in edges if e["confidence"] == "low"]
    if low:
        print(f"\nconfiança baixa ({len(low)}) — revisar:")
        for e in low[:20]:
            print(f"  ~ {e['from']} → {e['to']} ({e['relation']}) — {e.get('note') or 'sem nota'}")
        if len(low) > 20:
            print(f"  … e mais {len(low)-20}")
    if graph["warnings"]:
        print(f"\navisos ({len(graph['warnings'])}):")
        for w in graph["warnings"][:40]:
            print("  ! " + w)
        if len(graph["warnings"]) > 40:
            print(f"  … e mais {len(graph['warnings'])-40}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Consolida o mapa de integração dos repositórios clonados.")
    ap.add_argument("root", type=Path, help="pasta que contém os repositórios clonados")
    ap.add_argument("--out", type=Path, default=Path("integration-map"), help="pasta de saída")
    ap.add_argument("--template", type=Path, help="map.html modelo (padrão: ../assets/map.html)")
    ap.add_argument("--aliases", type=Path, help="aliases.yml para unificar ids do mesmo sistema")
    ap.add_argument("--depth", type=int, default=1, help="níveis de pasta a procurar (padrão 1)")
    ap.add_argument("--no-auto-merge", action="store_true",
                    help="não funde nó api.<host> com a aplicação de mesmo nome")
    ap.add_argument("--check", action="store_true", help="valida e sai; não escreve nada")
    args = ap.parse_args()

    root = args.root.expanduser()
    if not root.is_dir():
        sys.exit(f"pasta não encontrada: {root}")
    out = args.out.expanduser()

    graph, scans = build(root, out, args.aliases.expanduser() if args.aliases else None,
                         args.depth, auto_merge=not args.no_auto_merge)
    summarize(graph, scans)

    if args.check:
        return 1 if graph["warnings"] else 0

    out.mkdir(parents=True, exist_ok=True)
    (out / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    template = args.template or (Path(__file__).resolve().parent.parent / "assets" / "map.html")
    if not template.is_file():
        sys.exit(f"template não encontrado: {template}")
    inject(template, out / "map.html", graph)
    print(f"\nescrito: {out/'graph.json'}\nescrito: {out/'map.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
