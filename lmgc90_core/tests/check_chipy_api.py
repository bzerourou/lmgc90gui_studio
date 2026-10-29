#!/usr/bin/env python
"""Vérifie la config chipy de LMGC90_GUI Studio contre l'API chipy RÉELLE.

À lancer à la racine du monorepo, dans l'environnement qui possède pylmgc90 :

    python check_chipy_api.py                       # catalogues + scripts générés + macros
    python check_chipy_api.py --script command.py   # + un command.py existant
    python check_chipy_api.py --show ExSolver SetDimension   # signature / doc / source

Sans pylmgc90, seules les vérifications hors-API tournent (doublons, syntaxe,
doublons de détecteurs, détecteurs d'une autre dimension...).

Code retour : 0 si rien d'anormal, 1 sinon.
"""
from __future__ import annotations

import argparse
import ast
import inspect
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_DIALOG = Path("lmgc90_gui/src/lmgc90_gui/dialogs/chipy_routines_dialog.py")
CATALOGS = ("_INSP2D_FUNCS", "_INSP3D_FUNCS", "_INSPI_FUNCS", "_SET_FUNCS")
DET2D = ("CLALp", "CLJCx", "DKALp", "DKDKL", "DKDKx", "DKJCx", "DKKDx", "DKPLx",
         "P2P2L", "PLALp", "PLJCx", "PLPLx", "PTPT2")
DET3D = ("CDCDx", "CDPLx", "CSASp", "CSPRx", "PRASp", "PRPLx", "PRPRx", "PTPT3",
         "SPCDx", "SPDCx", "SPPLx", "SPPRx", "SPSPx")
PHANTOMS = ("DKMECAx", "ALpMECAx", "SPMECAx", "ALpALp", "NODES", "PT2Dx", "PT3Dx")
MACROS_TO_SHOW = ("ExSolver", "SetDimension", "SelectProxTactors", "ComputeFext",
                  "ComputeFreeVelocity", "ComputeDof", "WriteOut", "WriteDisplayFiles",
                  "ReadDatbox", "ReadIni", "OpenDisplayFiles")
MAILX_TOKENS = ("mecaMAILx", "therMAILx", "poroMAILx", "multiMAILx")

problems = 0


def bad(msg: str) -> None:
    global problems
    problems += 1
    print(f"  [X] {msg}")


def ok(msg: str) -> None:
    print(f"  [ok] {msg}")


def info(msg: str) -> None:
    print(f"  [i] {msg}")


# --------------------------------------------------------------------------
def load_chipy():
    try:
        from pylmgc90 import chipy  # type: ignore
        return chipy
    except Exception as exc:  # noqa: BLE001
        print(f"[!] pylmgc90.chipy non importable ({exc}) -> tests d'existence sautés\n")
        return None


def load_catalogs(path: Path) -> dict[str, list[tuple]]:
    """Lit les catalogues de la classe ChipyRoutinesDialog SANS importer PyQt6."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: dict[str, list[tuple]] = {}
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        for node in cls.body:
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id in CATALOGS):
                out[node.targets[0].id] = list(ast.literal_eval(node.value))
    return out


def chipy_names_in(source: str) -> Counter:
    names: Counter = Counter()
    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id == "chipy"):
            names[node.attr] += 1
    return names


def real_arity(fn) -> int | None:
    """Nb d'arguments positionnels (signature, sinon 1re ligne de la docstring)."""
    try:
        return len([p for p in inspect.signature(fn).parameters.values()
                    if p.default is p.empty])
    except (TypeError, ValueError):
        pass
    first = (fn.__doc__ or "").strip().splitlines()[:1]
    m = re.match(r"^[\w.]*\((.*?)\)", first[0]) if first else None
    if m is None:
        return None
    return len([a for a in m.group(1).split(",") if a.strip() and "=" not in a])


# --------------------------------------------------------------------------
def check_catalogs(chipy, path: Path) -> dict[str, list[tuple]]:
    print(f"== 1. Catalogues du dialogue ({path})")
    if not path.is_file():
        bad(f"fichier introuvable : {path} (utilisez --dialog)")
        return {}
    cats = load_catalogs(path)
    for name in CATALOGS:
        entries = cats.get(name, [])
        print(f" -- {name}: {len(entries)} entrées")
        counts = Counter(e[0] for e in entries)
        dups = {k: v for k, v in counts.items() if v > 1}
        if dups:
            bad(f"{len(dups)} doublon(s) : " + ", ".join(f"{k} x{v}" for k, v in sorted(dups.items())[:8])
                + (" ..." if len(dups) > 8 else ""))
        none = sorted({e[0] for e in entries if len(e) > 2 and e[2] is None})
        if none:
            bad(f"{len(none)} entrée(s) d'arité None (absentes de lmgc90_user_2025 selon le code) : "
                + ", ".join(none[:6]) + (" ..." if len(none) > 6 else ""))
        if chipy is None:
            continue
        missing = sorted({e[0] for e in entries if not hasattr(chipy, e[0])})
        if missing:
            bad(f"{len(missing)} nom(s) absents de chipy : " + ", ".join(missing[:10])
                + (" ..." if len(missing) > 10 else ""))
        mism = []
        for e in entries:
            if len(e) > 2 and isinstance(e[2], int) and hasattr(chipy, e[0]):
                ra = real_arity(getattr(chipy, e[0]))
                if ra is not None and ra != e[2]:
                    mism.append(f"{e[0]} (catalogue {e[2]}, chipy {ra})")
        if mism:
            bad(f"{len(mism)} arité(s) divergente(s) : " + "; ".join(mism[:6])
                + (" ..." if len(mism) > 6 else ""))
        if not (dups or none or missing or mism):
            ok("rien à signaler")
    return cats


# --------------------------------------------------------------------------
def make_project(dim: int):
    from lmgc90_core import Project, pre  # type: ignore
    p = Project(name=f"chk{dim}d", dimension=dim)
    p.add(pre.material(name="STEEL", materialType="RIGID", density=7800.0))
    p.add(pre.model(name="rigid", physics="MECAx",
                    element="Rxx2D" if dim == 2 else "Rxx3D", dimension=dim))
    if dim == 2:
        p.add(pre.rigidDisk(r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL"))
    else:
        p.add(pre.rigidSphere(r=0.1, center=[0.0, 0.0, 0.0], model="rigid", material="STEEL"))
    return p


def battery(cats: dict[str, list[tuple]]):
    def rows(name, **kw):
        return [{"func": e[0], "ids": "1", "group": "", "store": "res",
                 "step_mode": "all", "step_val": 1, **kw} for e in cats.get(name, [])]

    sets = [{"func": e[0], "args": "1", "step_mode": "all", "step_val": 1}
            for e in cats.get("_SET_FUNCS", []) if "Set" in e[0]]
    stress = {"insp2d_entries": rows("_INSP2D_FUNCS"), "insp3d_entries": rows("_INSP3D_FUNCS"),
              "inspi_entries": rows("_INSPI_FUNCS"), "set_entries": sets}
    legacy = {k: True for k in ("use_DKMECAx", "use_ALpMECAx", "use_SPMECAx", "use_PT2Dx", "use_PT3Dx")}
    adv = {"advanced_assemble_mechanical": True, "advanced_fd_select_prox": True,
           "advanced_compute_rnod": True, "advanced_fatal_damping": True,
           "advanced_smooth_force": True, "advanced_write_out_dof": True,
           "advanced_write_out_gpv": True, "advanced_write_last": True,
           "advanced_write_last_dof": True, "advanced_circular_selection": True,
           "advanced_set_contact_radius": True, "advanced_set_contact_radius_args": "0.01",
           "advanced_hdf5": True, "advanced_add_registers_to_display": True}
    cases = []
    for dim in (2, 3):
        cases += [
            (f"{dim}D défauts (dialogue jamais ouvert)", dim, {}),
            (f"{dim}D tous détecteurs + anciens alias", dim,
             {**{f"use_{n}": True for n in DET2D + DET3D}, **legacy}),
            (f"{dim}D critères d'arrêt disp_max", dim,
             {"use_stop_crit": True, "stop_crit_type": "disp_max"}),
            (f"{dim}D critères d'arrêt vel_max", dim,
             {"use_stop_crit": True, "stop_crit_type": "vel_max"}),
            (f"{dim}D options avancées", dim, adv),
            (f"{dim}D toutes inspections (stress catalogues)", dim, stress),
            (f"{dim}D restart + multi-pas", dim,
             {"use_restart": True, "restart_step": 10, "use_multi_step": True,
              "multi_step_nb": 2, "multi_step_sizes": "1e-3, 1e-4"}),
        ]
    return cases


def check_generated(chipy, cats) -> None:
    print("\n== 2. Scripts générés (lmgc90_core.compute_script)")
    try:
        from lmgc90_core import generate_command_script  # type: ignore
    except Exception as exc:  # noqa: BLE001
        bad(f"lmgc90_core non importable : {exc}")
        return
    for label, dim, params in battery(cats):
        print(f" -- {label}")
        try:
            script = generate_command_script(make_project(dim), params)
        except Exception as exc:  # noqa: BLE001
            bad(f"génération impossible : {type(exc).__name__}: {exc}")
            continue
        n0 = problems
        try:
            names = chipy_names_in(script)
        except SyntaxError as exc:
            bad(f"script invalide (ligne {exc.lineno}) : {exc.msg} -> {(exc.text or '').strip()[:70]!r}")
            continue
        if "chipy.ComputeFreeVelocity()" not in script:
            bad("aucun chipy.ComputeFreeVelocity() dans la boucle")
        other = DET3D if dim == 2 else DET2D
        for n in other:
            if f"chipy.{n}_SelectProxTactors" in script:
                bad(f"détecteur {n} (autre dimension) émis dans un projet {dim}D")
        for n in PHANTOMS:
            is_absent_module = n not in ("PT2Dx", "PT3Dx")
            if (f"{n}_SelectProxTactors" in script
                    or (is_absent_module and f"chipy.{n}_" in script)):
                bad(f"module inexistant émis : {n}")
        for det, c in Counter(re.findall(r"chipy\.(\w+_SelectProxTactors)\(", script)).items():
            if c > 1:
                bad(f"{det}() émis {c} fois")
        if chipy is not None:
            gone = sorted(a for a in names if not hasattr(chipy, a))
            if gone:
                bad(f"{len(gone)} nom(s) chipy inexistants : " + ", ".join(gone[:10])
                    + (" ..." if len(gone) > 10 else ""))
        if problems == n0:
            ok("rien à signaler")


def check_scripts(chipy, files: list[str]) -> None:
    print("\n== 3. Scripts fournis")
    for f in files:
        print(f" -- {f}")
        try:
            names = chipy_names_in(Path(f).read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as exc:
            bad(f"illisible/invalide : {exc}")
            continue
        if chipy is None:
            info(f"{len(names)} appels chipy distincts (existence non testée)")
            continue
        gone = sorted(a for a in names if not hasattr(chipy, a))
        bad("inexistants : " + ", ".join(gone)) if gone else ok(f"{len(names)} appels, tous présents")


def check_macros(chipy) -> None:
    print("\n== 4. Les macros couvrent-elles déjà les MAILx ? (doublons possibles)")
    if chipy is None:
        info("chipy indisponible")
        return
    for name in ("ComputeFext", "ComputeBulk", "ComputeFreeVelocity", "ComputeDof",
                 "UpdateStep", "WriteDisplayFiles"):
        fn = getattr(chipy, name, None)
        if fn is None:
            bad(f"chipy.{name} n'existe pas")
            continue
        try:
            src = inspect.getsource(fn)
        except (OSError, TypeError):
            info(f"{name}: source indisponible (fonction compilée) -> lire --show {name}")
            continue
        found = [t for t in MAILX_TOKENS if t in src]
        if found:
            info(f"{name}: la macro appelle déjà {', '.join(found)} "
                 f"-> les appels explicites du générateur font doublon")
        else:
            info(f"{name}: la macro ne mentionne aucun MAILx -> appels explicites nécessaires")


def show(chipy, names: list[str]) -> None:
    print("== Détails")
    if chipy is None:
        print("  chipy indisponible")
        return
    for n in names or MACROS_TO_SHOW:
        fn = getattr(chipy, n, None)
        print(f"\n--- chipy.{n}")
        if fn is None:
            print("  N'EXISTE PAS")
            continue
        try:
            print("  signature:", inspect.signature(fn))
        except (TypeError, ValueError):
            pass
        print("  doc:", (fn.__doc__ or "(aucune)").strip()[:400])
        try:
            print("  source (début):\n    " + "\n    ".join(inspect.getsource(fn).splitlines()[:25]))
        except (OSError, TypeError):
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dialog", type=Path, default=DEFAULT_DIALOG)
    ap.add_argument("--script", action="append", default=[], help="command.py à tester (répétable)")
    ap.add_argument("--show", nargs="*", help="affiche signature/doc/source de ces noms chipy")
    ap.add_argument("--no-generate", action="store_true", help="saute l'étape 2")
    args = ap.parse_args()

    chipy = load_chipy()
    if args.show is not None:
        show(chipy, args.show)
        return 0
    cats = check_catalogs(chipy, args.dialog)
    if not args.no_generate:
        check_generated(chipy, cats)
    if args.script:
        check_scripts(chipy, args.script)
    check_macros(chipy)
    print(f"\n{'AUCUN problème' if not problems else str(problems) + ' problème(s) relevé(s)'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())