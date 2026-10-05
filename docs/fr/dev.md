# LMGC90_GUI Studio — Architecture & Guide du Contributeur

> Monorepo `lmgc90gui_studio` : **`lmgc90_core`** 0.1.x · **`lmgc90_engine`** 0.1.x · **`lmgc90_gui`** 0.1.x (fenêtre « v0.6.x »).
> Cette révision remplace l'ancien guide « MVC monolithique » (`src/core`, `ProjectState`, `_pylmgc_bodies`, mixins du contrôleur). Les correspondances ancien → nouveau sont données au §1.2.

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Structure des fichiers](#2-structure-des-fichiers)
3. [`lmgc90_core` — le modèle scientifique](#3-lmgc90_core--le-modèle-scientifique)
4. [`lmgc90_engine` — le pont pylmgc90](#4-lmgc90_engine--le-pont-pylmgc90)
5. [`lmgc90_gui` — le client PyQt6](#5-lmgc90_gui--le-client-pyqt6)
6. [Flux de données](#6-flux-de-données)
7. [Systèmes clés](#7-systèmes-clés)
8. [Cycle de vie d'un projet](#8-cycle-de-vie-dun-projet)
9. [Conventions et patterns](#9-conventions-et-patterns)
10. [Guide de contribution](#10-guide-de-contribution)
11. [Tests](#11-tests)
12. [Points de vigilance connus](#12-points-de-vigilance-connus)

---

## 1. Vue d'ensemble

### 1.1 Trois paquets, une seule direction de dépendance

```
┌──────────────────────────────────────────────────────────────┐
│  lmgc90_gui   (PyQt6)                                        │
│  vues · onglets · assistants · ProjectController (façade)    │
└───────────────┬──────────────────────────────────────────────┘
                │ dépend de
┌───────────────▼──────────────────────────────────────────────┐
│  lmgc90_engine   (pylmgc90 optionnel, pas de Qt)             │
│  EngineSession · materialize · DATBOX · dépôt pylmgc         │
└───────────────┬──────────────────────────────────────────────┘
                │ dépend de
┌───────────────▼──────────────────────────────────────────────┐
│  lmgc90_core   (numpy seul, pas de Qt, pas de pylmgc90)      │
│  Project · entités · historique · validation · scripts       │
└──────────────────────────────────────────────────────────────┘
```

| Paquet | Rôle | Dépendances |
|---|---|---|
| `lmgc90_core` | Source de vérité : `Project`, entités, `CommandHistory` (undo/redo), validation, générateurs numpy, sérialisation `.lmgc90` + sidecar `.npz`, émission `pre.py` / `command.py` / `run.sbatch`, scènes d'exemple. | `numpy` |
| `lmgc90_engine` | `Project` → vrais objets `pylmgc90.pre`, écriture DATBOX, `pre.visuAvatars`, dépôt granulo pylmgc. | `lmgc90_core`, `numpy`, `pylmgc90` *(optionnel)* |
| `lmgc90_gui` | Client Qt : onglets CRUD, assistants, viewer 3D PyVista, journal, calcul. | `lmgc90_core`, `lmgc90_engine`, `PyQt6` ; `pyvista`/`pyvistaqt` *(optionnels)* |

### 1.2 Règles d'architecture (non négociables)

- **Pureté** : `lmgc90_core` n'importe jamais `pylmgc90`, `PyQt6`, `pyvista`, `gmsh`, `vtk` (garanti par `lmgc90_core/tests/test_purity.py`). Le moteur n'importe `pylmgc90` que dans des fonctions (`test_engine_purity.py`).
- **Identité = `avatar_id` / `population_id`**, jamais un indice de liste.
- **Le contrôleur ne possède aucun objet pylmgc90.** Les objets « live » vivent dans `EngineSession` après `materialize()`.
- **Une seule source de rafraîchissement** : le signal `state_changed`.
- **Pas de logique métier dans les onglets** : ils appellent `controller.*`.
- **AoS vs SoA** : `Avatar` = édition fine ; `ParticlePopulation` = génération de masse (SoA est le comportement **par défaut** du dépôt, plus une case à cocher).
- **`pre.py` généré = artefact de reproductibilité** (plus que le JSON).

### 1.3 Correspondance ancienne → nouvelle architecture

| Ancien (MVC monolithique) | Nouveau |
|---|---|
| `src/core/models.py` (`ProjectState`) | `lmgc90_core/entities.py` + `lmgc90_core/project.py` (`Project`) |
| `src/core/validators.py` | `lmgc90_core/validate.py` (fonctions `validate_*`) |
| `src/core/generators.py` | `lmgc90_core/generate.py` (`loop_positions`, `expand_loop`, `expand_for_loop`, `NumpyGranulo`) |
| `src/core/particle_population*.py` | `lmgc90_core/population.py` + `lmgc90_core/io.py` (sidecar) |
| `src/core/serializers.py` | `lmgc90_core/io.py` |
| `src/core/pylmgc_bridge.py` (`LMGC90Bridge`) | `lmgc90_engine/materialize.py` + `avatar_factory.py` |
| `src/utils/script_generator.py` | `lmgc90_core/pre_script.py` (`emit_pre`) |
| `src/utils/compute_script_generator.py` | `lmgc90_core/compute_script.py` (shim déprécié côté GUI) |
| `src/utils/fast_granulo_engin.py` | `NumpyGranulo` (core) — il n'y a plus de moteur « fast » séparé |
| `controllers/*_mixin.py`, `_pylmgc_*` | `ProjectController` mince + `EngineSession` |
| `controller.state` | `controller.project` |
| `pre.*` pylmgc90 dans la GUI | `lmgc90_core.pre` (fabriques pures aux mêmes kwargs) |
| `avatar[i]` positionnel | toujours exposé en safe_eval, mais l'identité réelle est `avatar_id` |
| Case à cocher « SoA » | `Project.deposit` produit toujours une `ParticlePopulation` |
| Particle Factory, Convertisseur de script, Templates, Assistants projet/granulo | **non portés** dans la version actuelle |

---

## 2. Structure des fichiers

```
lmgc90gui_studio/
├── README.md / README_fr.md / README_INSTALL.md
├── install.ps1                    # core → engine → gui[qt]
├── pyproject.toml                 # méta (ne remplace PAS les 3 paquets)
├── docs/fr/                       # documentation utilisateur + technique
│
├── lmgc90_core/
│   ├── pyproject.toml
│   ├── examples/                  # granular_box.py, uniaxial_compression.py
│   ├── tests/                     # test_purity, test_project, test_population, ...
│   └── src/lmgc90_core/
│       ├── __init__.py            # API publique (Project, pre, entités, ...)
│       ├── types.py               # enums + schémas (matériaux, lois, éléments)
│       ├── ids.py                 # avatar_id / population_id / id de particule
│       ├── errors.py              # LMGC90Error, ValidationError, ...
│       ├── entities.py            # Material, Model, Avatar, ContactLaw, ...
│       ├── population.py          # ParticlePopulation (SoA)
│       ├── project.py             # Project (agrégat + API add/undo/save)
│       ├── commands.py            # Command, CommandHistory
│       ├── validate.py            # validate_material/model/avatar/...
│       ├── pre.py                 # fabriques « comme pylmgc90.pre »
│       ├── generate.py            # boucles, ForLoop, NumpyGranulo
│       ├── masonry.py             # MasonryConfig, expand_masonry
│       ├── io.py                  # .lmgc90 JSON + .populations.npz
│       ├── pre_script.py          # emit_pre / emit_equivalent
│       ├── chipy_script.py        # emit_chipy
│       ├── compute_script.py      # ComputeScriptGenerator (command.py)
│       ├── pipeline.py            # Pipeline, render_sbatch
│       ├── numpy_compat.py        # patch np.cross (NumPy 2 / 2D)
│       ├── scenes/                # scènes de démonstration pures
│       └── data/meshes/Carre.msh
│
├── lmgc90_engine/
│   ├── pyproject.toml
│   ├── examples/session_demo.py
│   ├── tests/
│   └── src/lmgc90_engine/
│       ├── session.py             # EngineSession
│       ├── materialize.py         # Project → conteneurs pre + MaterializedScene
│       ├── avatar_factory.py      # Avatar/Population → corps pre
│       ├── granulo.py             # dépôt pylmgc90 → ParticlePopulation
│       ├── datbox.py              # writeDatbox, DATBOX dual (cellule)
│       └── errors.py
│
└── lmgc90_gui/
    ├── pyproject.toml             # extras [qt] [viz] [dev]
    ├── main.py
    ├── examples/                  # headless_demo.py, wave1_scene.py
    ├── tests/
    └── src/lmgc90_gui/
        ├── app.py                 # main() + QApplication
        ├── controller/
        │   ├── project_controller.py
        │   └── signals.py         # pyqtSignal ou stubs sans Qt
        ├── views/
        │   ├── main_window.py     # create_main_window()
        │   ├── tree_view.py       # Model tree (lecture seule)
        │   ├── history_dock.py    # pile de commandes + Undo/Redo
        │   ├── viewer_3d.py       # Viewer3D (PyVista)
        │   ├── styles.py
        │   ├── widgets/entity_tree.py
        │   └── tabs/              # material, model, avatar, loop, for_loop,
        │                          # granulo, contact, visibility, dof, postpro,
        │                          # viewer, groups, contactors, deformable,
        │                          # masonry, compute  (+ base_tab.py)
        ├── dialogs/               # wizards, préférences, journal, palette, ...
        ├── workers/               # compute_worker, datbox_worker, materialize_worker
        ├── examples/              # catalogue ExampleSpec (métadonnées)
        ├── utils/                 # safe_eval, eval_context, preferences,
        │                          # app_journal, naming, field_forms, scene_geometry
        └── resources/
```

---

## 3. `lmgc90_core` — le modèle scientifique

### 3.1 `types.py` — vocabulaire LMGC90

Enums (valeurs = noms `pylmgc90`) : `MaterialType`, `AvatarType`, `ContactLawType`, `AvatarOrigin` (`MANUAL`, `LOOP`, `GRANULO`, `FACTORY`), `UnitSystem`.

Tables de référence qui pilotent validation **et** formulaires GUI :

| Constante | Usage |
|---|---|
| `ELEMENTS_BY_PHYSICS[physique][dim]` | éléments autorisés (validation + `ModelTab`) |
| `MATERIAL_PROPERTY_SCHEMA`, `MATERIAL_PROPERTY_CHOICES`, `ORTHOTROPIC_FIELDS_2D/3D`, `ISOTROPIC_FIELDS` | champs de `MaterialTab` |
| `CONTACT_LAW_PROPERTY_SCHEMA`, `CONTACT_LAW_CATEGORIES` | champs de `ContactTab`, validation des lois |
| `CONTACTORS_RIGID_2D/3D`, `CONTACTORS_MESH_2D/3D` | formes de contacteurs compatibles |
| `RIGID_AVATARS_2D/3D`, `DEFORMABLE_2D/3D` | cohérence avatar ↔ modèle |
| `POPULATION_TYPES` | types éligibles au SoA (disque, sphère, disque discret, cluster, cylindre, polygone, polyèdre) |
| `LOOP_ALIASES` | noms de boucles (FR/EN) → canoniques |

### 3.2 `entities.py` — entités sérialisables

Dataclasses sans dépendance Qt/pylmgc : `Material`, `Model`, `Avatar`, `ContactLaw`, `VisibilityRule`, `DOFOperation`, `PostProCommand`, `Loop`, `ForLoop`, `GranuloConfig`. Chacune expose `to_dict()` / `from_dict()`.

```python
@dataclass
class Avatar:
    avatar_type: AvatarType
    center: list[float]
    material_name: str
    model_name: str
    color: str = "BLUEx"
    origin: AvatarOrigin = AvatarOrigin.MANUAL
    avatar_id: str = field(default_factory=new_avatar_id)   # stable
    radius: Optional[float] = None
    axis: Optional[dict] = None              # axe1/axe2/axe3
    vertices, nb_vertices, generation_type, is_hollow
    wall_params, contactors, mesh_params
```

`GranuloConfig` = **intention** d'un dépôt (les tableaux vivent dans `ParticlePopulation`). `create_avatars=False` = « distribution seule » (rayons échantillonnés dans `config.radii`, aucune population).

### 3.3 `ids.py`

```python
new_avatar_id()                 # uuid4 hex
new_population_id()            # "pop_" + uuid4 hex
particle_id(pop_id, i)         # "pop_xxx:42"
parse_particle_id("pop_xxx:42") # → ("pop_xxx", 42)
```

### 3.4 `validate.py`

Fonctions levant `ValidationError` : `validate_material`, `validate_model`, `validate_avatar(avatar, model)`, `validate_contact_law`, `validate_visibility(rule, law_names)`, plus `compatible_contactors(type, dim)` et `is_shape_compatible`. Règles clés : noms ≤ 5 caractères, densité > 0, élément valide pour (physique, dimension), avatar rigide ↔ `Rxx2D/Rxx3D`, contacteurs de 5 caractères.

### 3.5 `Project` et `CommandHistory`

```python
p = Project(name="box", dimension=2)
p.add(pre.material(name="STEEL", materialType="RIGID", density=7800))   # valide + journalise
p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
av = p.add(pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL"))
p.undo(); p.redo()
```

Champs principaux : `materials, models, avatars, populations, laws, visibility, operations, postpro, loops, for_loops, granulo, avatar_groups, population_groups, dynamic_vars, history`.

Points d'entrée :

| Méthode | Rôle |
|---|---|
| `add(obj, on_conflict=None)` | dispatch par type ; valide ; exécute une `Command`. `on_conflict` ∈ `error` (défaut) · `skip` · `merge` |
| `group(name, ids)` / `remove_avatar(id)` | groupes et suppression (commandes `SetGroup`, `RemoveAvatar`) |
| `deposit(config)` | dépôt numpy → **une** `ParticlePopulation` ; ou rayons seuls si `create_avatars=False` |
| `apply_loop`, `apply_for_loop`, `apply_masonry` | génération d'avatars/entités |
| `undo()` / `redo()` / `journal()` | historique |
| `save(path)` / `Project.load(path)` | `.lmgc90` + sidecar |
| `to_pre_script()` / `to_chipy_script(**params)` / `sbatch(**slurm)` / `equivalent(obj)` | exports |
| `n_bodies`, `summary()` | statistiques |

`commands.py` définit une `Command` (`apply`, `revert`, `describe`, `to_journal`) par action : `AddMaterial`, `AddModel`, `AddAvatar`, `RemoveAvatar`, `AddPopulation`, `AddLaw`, `AddSeeTable`, `AddDOF`, `AddPostPro`, `AddLoop`, `SetGroup`. Granularité voulue : **une population = une commande**, **une boucle = une commande**. `CommandHistory` (limite 200) sérialise ses piles (`to_dict` / `load_stacks`).

### 3.6 `pre.py` — fabriques « comme pylmgc90 »

Mêmes noms/kwargs que `pylmgc90.pre`, mais retournent des dataclasses pures : `material`, `model`, `rigidDisk`, `rigidSphere`, `rigidJonc`, `rigidPolygon`, `rigidCluster`, `rigidCylinder`, `rigidPlan`, `rigidPolyhedron`, `rigidOvoidPolygon`, `rigidDiscreteDisk`, `smoothWall`, `roughWall`, `fineWall`, `granuloRoughWall`, `roughWall3D`, `granuloRoughWall3D`, `emptyAvatar`, `meshed_rectangle`, `tact_behav`, `see_table`.

```python
from lmgc90_core import pre
pre.see_table(CorpsCandidat="RBDY2", candidat="DISKx", colorCandidat="BLUEx",
              CorpsAntagoniste="RBDY2", antagoniste="JONCx", colorAntagoniste="GRAYx",
              behav="IQS01", alert=0.05)
```

### 3.7 `generate.py`, `masonry.py`

- `loop_positions` / `expand_loop` : cercle, grille (carrée), ligne, spirale ; clone le template (`copy()`, nouvel `avatar_id`, `origin=LOOP`).
- `expand_for_loop` : expressions `expr_x/y/z/radius` évaluées par `_safe_arith` (arithmétique AST restreinte). Les autres cibles de `ForLoop` (`material`, `model`, `dof`, `visibility`, `granulo`, `granulo_dist`) sont gérées dans `Project.apply_for_loop`.
- `NumpyGranulo.deposit(config)` : rejet par lots vectorisés, conteneurs `Box2D`, `Disk2D/Drum2D`, `Couette2D`, `Box3D`, `Sphere3D`, `Cylinder3D`. Déterministe avec `seed`.
- `expand_masonry(MasonryConfig)` : appareils `standard`, `running`, `stack`, `flemish`, `paneresse_simple`, `paneresse_double` ; briques = `rigidPolygon` (2D) ou `rigidPolyhedron` (8 sommets, 3D).

### 3.8 `population.py` — SoA

Voir [Populations de particules](particle_population.md).

### 3.9 `io.py` — persistance

Schéma `.lmgc90` **v2** (migration v1→v2 incluse). Voir §7.3 et la page `particle_population.md` pour le sidecar.

### 3.10 Scripts

| Module | Sortie |
|---|---|
| `pre_script.emit_pre(project)` | `pre.py` auditable (inclut `PRE_PY_CROSS_PATCH` NumPy 2) |
| `compute_script.ComputeScriptGenerator` / `generate_command_script` | `command.py` chipy complet (détecteurs, extraction, inspection, restart, critère d'arrêt, multi-pas) |
| `chipy_script.emit_chipy(project, **params)` | complète les défauts puis délègue au générateur |
| `pipeline.Pipeline.standard(...)`, `render_sbatch(...)` | pipeline en données + script SLURM |

### 3.11 `scenes/`

`scenes/demos.py` : fonctions `f(project) -> None` (« scène pure », sans `pre`, sans engine) enregistrées dans `SCENE_BUILDERS`. Helpers dans `scenes/_common.py` (`ensure_rigid_2d`, `iqs`, `see_table`, `disk`, `smooth_wall`, `mesh_rect`…). Les dépôts sont déclarés par `project.granulo.append(GranuloConfig(...))` ; c'est `ProjectController.apply_scene` qui les résout ensuite.

---

## 4. `lmgc90_engine` — le pont pylmgc90

### 4.1 `EngineSession`

```python
session = EngineSession(project)
session.available()                 # pylmgc90 importable ?
session.materialize(force=False)    # → MaterializedScene (lève PylmgcNotAvailable)
session.write_datbox("DATBOX")
session.emit_pre_script("pre.py")   # toujours disponible (délègue au core)
session.emit_chipy_script("command.py", dt=1e-3, nb_steps=5000)
session.export_all(dir, try_datbox=True)
session.visu_avatars()              # pre.visuAvatars sur les corps dessinables
session.run_granulo(config)         # dépôt pylmgc → ParticlePopulation
session.mark_dirty(); session.dirty; session.body_map; session.population_map
```

Un drapeau `dirty` permet de différer `materialize()` (thread de travail). Le contrôleur appelle `mark_dirty()` après chaque mutation.

### 4.2 `materialize.py`

`materialize_project(project) -> MaterializedScene` construit dans l'ordre : matériaux → modèles → avatars AoS → populations → lois → see-tables → opérations DOF → post-traitement. `MaterializedScene` contient les six conteneurs `pre.*` et les cartes d'identité :

```python
body_by_avatar_id: dict[str, body]
bodies_by_population_id: dict[str, list[body]]
material_by_name, model_by_name, law_by_name
```

`_make_material` normalise les options vers l'API pylmgc90 (alias `alpha→dilatation`, `sigc→iso_hard`, orthotropie en listes, `DISCRETE` en vecteurs, etc. ; voir `lmgc90_engine/tests/test_material_properties.py`). `_apply_dof` n'accepte que les kwargs connus et retire les métadonnées Studio (`phase`, …).

### 4.3 `avatar_factory.py`

`build_avatar(av, materials=, models=)` : un `if` par `AvatarType` (disque, sphère, jonc, polygone, polyèdre, cluster, cylindre, plan, murs 2D/3D, maillé, avatar vide/brique). `build_population_bodies(pop, ...)` : une boucle `pre.rigidXxx` par particule (limite structurelle de pylmgc90). `_apply_contactors` attache les contacteurs (traduction `POLYG/POLYR` régulier/plein, `shift`, groupes de maillage). `resolve_mesh_filepath` convertit `.brep/.step/.iges/.geo` en `.msh` via **gmsh** (optionnel).

### 4.4 `granulo.py`, `datbox.py`

- `deposit_population(config)` appelle `pre.depositInBox2D/3D`, `…Drum2D/Disk2D`, `…Couette2D`, `…Sphere3D`, `…Cylinder3D` et retourne une `ParticlePopulation`.
- `datbox.write_datbox(scene, path)` applique `patch_numpy_cross()` puis `pre.writeDatbox(...)`. `write_cell_dual_datbox` écrit `DATBOX_SPRD/` + `DATBOX_STBL/` + `PHASES.json` (scènes « cellule »). `export_pre_script` ne nécessite pas pylmgc90.

### 4.5 Erreurs

`EngineError` ← `PylmgcNotAvailable`, `MaterializationError`, `UnknownBodyError`, `DatboxError`.

---

## 5. `lmgc90_gui` — le client PyQt6

### 5.1 `ProjectController`

Façade mince (`QObject` si Qt présent, sinon objet simple grâce à `signals.py`) :

```python
ctrl = ProjectController()          # fonctionne sans Qt (tests headless)
ctrl.project                         # lmgc90_core.Project
ctrl.session                         # EngineSession
ctrl.prefs, ctrl.journal             # Preferences, AppJournal
ctrl.state_changed / project_loaded / error_occurred   # Signal
with ctrl.batch(): ...               # un seul state_changed à la sortie
```

Familles de méthodes :

| Famille | Méthodes |
|---|---|
| Projet | `new_project`, `load_project`, `save_project`, `apply_scene(builder, on_conflict=)` |
| Ajout générique | `add(obj)` + `add_material/model/avatar/law/visibility/dof/postpro/population` |
| Édition | `update_material/model/law/avatar/visibility/dof`, `remove_*` |
| Génération | `deposit`, `run_granulo_pylmgc`, `apply_loop`, `apply_for_loop`, `apply_masonry` |
| Groupes / variables | `group`, `remove_group`, `set_dynamic_var`, `remove_dynamic_var` |
| Historique | `undo`, `redo` |
| Export / moteur | `emit_pre_script`, `emit_chipy_script`, `export_all`, `prepare_run_directory`, `materialize`, `write_datbox`, `visu_avatars`, `pylmgc_available` |
| Préférences | `save_preferences`, `set_work_dir`, `work_dir` |

Toute erreur de validation est journalisée, émise via `error_occurred` puis relancée.

### 5.2 Vues

- **`main_window.create_main_window(controller)`** : menus (Fichier, Projet, Édition, Outils, Calcul, Onglets, Exemples, Aide), barre d'outils, dock *Model tree* (gauche), dock *History* (droite), registre `all_tabs` (id → titre, widget, icône).
- **Onglets par défaut** : `material, model, avatar, contact, visibility, dof, viewer`. `material` et `model` sont **essentiels** (non fermables). `Ctrl+1..9` ouvrent les neuf premiers de la liste Onglets → Ouvrir.
- **`tree_view`** : lecture seule ; il ne connaît pas encore de nœud dédié aux populations autre que « Populations (SoA) ».
- **`history_dock`** : liste `project.history.describe_stack()` + boutons Undo/Redo.
- **`viewer_3d.Viewer3D`** : rendu paramétrique PyVista ; modes Nav / Sélection / Règle ; couleurs LMGC90 / type / matériau / origine ; DOF et lois (see-tables) en surimpression ; export PNG. Le rafraîchissement est **manuel** (bouton *Rafraîchir la scène*).

### 5.3 Onglets : pattern « factory »

Chaque onglet est une **fonction** `create_xxx_tab(parent=None)` qui importe PyQt6 localement et retourne une classe `QWidget + BaseTab`. Ainsi `import lmgc90_gui` ne requiert pas Qt.

```python
def create_xxx_tab(parent=None):
    from PyQt6.QtWidgets import QWidget, ...
    class XxxTab(QWidget, BaseTab):
        def on_state_changed(self): ...   # relit controller.project
    return XxxTab(parent)
```

`BaseTab` fournit `bind_controller` (connexion à `state_changed`), `eval_float/eval_int/eval_list/eval_dict` (virgule décimale FR acceptée, expressions via `safe_eval`), `add_expression_help_label`. Les onglets de liste utilisent `widgets/entity_tree.create_entity_tree`. Les noms par défaut (≤ 5 caractères) viennent de `utils/naming.py` (`unique_name`, `suggest_*_name`).

### 5.4 Dialogues et assistants

Même pattern `create_*_dialog(...)` : `mesh_wizard` (corps déformables), `masonry_wizard`, `dynamic_vars_dialog`, `pipeline_dialog` (SLURM), `preferences_dialog`, `chipy_routines_dialog` (7 onglets : Modèle, Routines, Extraction, Pilotage, Inspect. 2D/3D/Interact.), `compute_log_dialog`, `journal_dialog`, `examples_dialog`, `link_visibility_dialog`, `command_palette_dialog` (`Ctrl+K`), `about_dialog`.

### 5.5 Workers

`compute_worker` (sous-processus `python command.py`, signaux `line_out/finished/failed`), `datbox_worker` (pre.py + command.py + DATBOX hors thread UI), `materialize_worker`. Pattern `Runner` = `QThread` + `QObject` déplacé dans le thread.

### 5.6 Utils

| Module | Rôle |
|---|---|
| `safe_eval.py` | évaluateur AST restreint (opérateurs, comparaisons, `if` ternaire, compréhensions à une clause `for`, appels sur noms du contexte, attributs non privés) |
| `eval_context.py` | `build_eval_context(project)` : `avatar[i]`, `group[...]`, `material[...]`, `model[...]`, `avatars_by_*`, math/numpy + variables dynamiques résolues dans l'ordre |
| `preferences.py` | `Preferences` (JSON `~/.lmgc90_gui/preferences.json`) |
| `app_journal.py` | journal circulaire + fichier optionnel |
| `field_forms.py` | schémas de paramètres d'avatars/DOF, `parse_vertices` |
| `scene_geometry.py` | géométrie 2D schématique (sous-échantillonne les grosses populations) |
| `compute_script_generator.py` | **shim déprécié** → `lmgc90_core.compute_script` |

### 5.7 Exemples

`lmgc90_gui/examples/__init__.py` ne contient que des **métadonnées** (`ExampleSpec(id, title, category, description, dimension, difficulty, scene, tags)`) ; la géométrie est dans `lmgc90_core.scenes`. Une assertion au chargement vérifie `SCENE_BUILDERS[id] is spec.scene`. Le chargement passe par `MainWindow._load_example` :

- **Remplacer** : `new_project(id, dim)` puis `apply_scene(scene)`.
- **Ajouter** : même dimension requise ; `apply_scene(scene, on_conflict="merge")`, historique conservé.

---

## 6. Flux de données

### 6.1 Création d'un avatar

```
AvatarTab._on_add()
  → pre.rigidDisk(...)                         # entité pure
  → controller.add_avatar(av) → controller.add(av)
      → Project.add(av) → _check_avatar (modèle/matériau existent, validate_avatar)
      → _run(AddAvatar) → CommandHistory.do → Project._insert_avatar
      → session.mark_dirty()
      → state_changed.emit()
  → tous les onglets / tree / history se relisent depuis controller.project
```

### 6.2 Dépôt granulométrique

```
GranuloTab._on_deposit()
  → GranuloConfig(...)
  ├─ « distribution seule »     → controller.deposit → Project.deposit (rayons dans config.radii)
  ├─ case « pylmgc »            → controller.run_granulo_pylmgc → session.run_granulo
  │                                → engine.deposit_population → project.add(population)
  └─ défaut                     → controller.deposit
                                   ├─ pylmgc dispo → session.run_granulo (repli numpy si échec)
                                   └─ sinon        → Project.deposit → NumpyGranulo
```

### 6.3 Sauvegarde / chargement

```
save_project(path)
  → io.save_project: project_to_dict → JSON (.lmgc90)
  → save_populations_sidecar(project.populations) → <nom>.populations.npz
  → data["particle_populations_sidecar"] = "<nom>.populations.npz"

load_project(path)
  → io.load_project: valide le schéma, migre v1→v2
  → fusionne meta JSON + arrays .npz → ParticlePopulation
  → reconstruit les listes d'entités (Project(record=False)), restaure les piles d'historique
```

Contrairement à l'ancienne version, il n'y a **pas** de « reconstruction des objets pylmgc90 au chargement » : la matérialisation est paresseuse (`session.materialize()` au moment du DATBOX / de `visuAvatars`).

### 6.4 Calcul

```
ComputeTab (dt, solveur, E/S) + ChipyRoutinesDialog (routines, extraction, pilotage)
  → get_parameters() → controller.prepare_run_directory / emit_chipy_script
       → pre.py + command.py (+ DATBOX si pylmgc dispo et auto_write_datbox)
  → create_compute_worker → subprocess « python command.py » (cwd = répertoire)
  → lignes → journal de calcul + journal applicatif
```

---

## 7. Systèmes clés

### 7.1 Identité

Un `Avatar` garde le même `avatar_id` toute sa vie ; groupes, DOF (`target_value`), `Loop.model_avatar_id`, post-traitement s'y réfèrent. Une particule SoA a un id **dérivé** `"{population_id}:{i}"` (jamais stocké).

Exception documentée : en `safe_eval`, `avatar[i]` est positionnel (commodité d'écriture dans les formulaires).

### 7.2 Variables dynamiques

`project.dynamic_vars` : nom → expression (ou nombre). Évaluées **dans l'ordre d'insertion** par `resolve_dynamic_vars` ; une expression non évaluable reste une chaîne. Persistées dans le `.lmgc90`. Les populations SoA **ne sont pas** exposées dans `avatar[...]` / `group[...]`.

### 7.3 Historique (undo/redo)

`Project.history` sauvegarde ses piles dans le `.lmgc90` (clé `history`) et un `journal` lisible. Le dock *History* affiche `describe()` de chaque commande.

### 7.4 Préférences

`Preferences` (dataclass) : paramètres chipy (`dt`, `nb_steps`, `theta`, `tol`, …), environnement (`python_executable`, `work_directory`, `projects_directory`, `auto_write_datbox`, `confirm_run`), autosave, récents, performance (`show_avatars_in_tree`, `max_tree_avatars`, …), viewer. `chipy_params()` alimente `emit_chipy_script`.

### 7.5 Conflits de noms (`on_conflict`)

`error` (défaut) · `skip` (réutilise matériau/modèle/loi existants, ignore see-tables/post-pro dupliqués) · `merge` (idem + union des groupes). Utilisé par « Ajouter au projet » des exemples.

---

## 8. Cycle de vie d'un projet

```
1. File → New              controller.new_project(name, dimension)  → Project + EngineSession neufs
2. Configuration           onglets → controller.add_* (undoable)
3. Sauvegarde              Ctrl+S → .lmgc90 (+ .populations.npz)
4. Scripts / DATBOX        Computation → Generate DATBOX / scripts (Ctrl+F5)
                           Tools → Generate pre.py / command.py / Export all
5. Calcul                  F5 → onglet Compute → sous-processus chipy
6. Rechargement            File → Open → io.load_project
```

---

## 9. Conventions et patterns

| Élément | Convention | Exemple |
|---|---|---|
| Classes | PascalCase | `ProjectController`, `ParticlePopulation` |
| Factories Qt | `create_*_tab/dialog/wizard` | `create_material_tab()` |
| Slots Qt | préfixe `_on_` | `_on_add` |
| Entités core | sans état Qt/pylmgc | `Material`, `Avatar` |
| Noms LMGC90 | ≤ 5 caractères (matériau, modèle, loi, couleur, shape) | `STEEL`, `rigid`, `BLUEx` |
| Imports lourds | locaux (dans les fonctions) | `from PyQt6...` dans `create_*` |

Gestion d'erreur côté vue : `try/except (ValidationError, ValueError)` → `QMessageBox.warning`. Le contrôleur relance après avoir émis `error_occurred`.

---

## 10. Guide de contribution

### Ajouter un type d'avatar

1. `types.py` : valeur d'`AvatarType`, et ajout à `RIGID_AVATARS_2D/3D` si rigide ; contacteurs compatibles si besoin.
2. `pre.py` : fabrique `rigidXxx(...)`.
3. `validate.py` : cas dans `_check_geometry`.
4. `pre_script.py` : cas dans `_emit_avatar` (sinon `av = None` + TODO).
5. `lmgc90_engine/avatar_factory.py` : cas dans `build_avatar`.
6. GUI : `utils/field_forms.AVATAR_PARAM_SCHEMA`, `AvatarTab._build`, `viewer_3d._MESH_BUILDERS`, `scene_geometry.avatar_to_geoms`, `visibility_tab._AVATAR_CONTACTORS`.
7. *(SoA)* `types.POPULATION_TYPES`, `population._validate_extra`, `avatar_factory.build_population_bodies` (`fn_map`), `pre_script._emit_population`.
8. Tests : core (validation), engine (stub de `pre`), GUI headless.

### Ajouter une loi de contact

`types.ContactLawType` + catégorie dans `CONTACT_LAW_CATEGORIES` + `CONTACT_LAW_PROPERTY_SCHEMA` (la `ContactTab` construit son formulaire à partir de ce schéma). L'engine transmet `properties` en kwargs à `pre.tact_behav` (`_make_law`).

### Ajouter un type de matériau / une option

`types.MATERIAL_PROPERTY_SCHEMA` (+ `MATERIAL_PROPERTY_CHOICES`), puis `engine/materialize._MATERIAL_OPTIONS` et `_MATERIAL_PROP_ALIASES`. Ajouter un test dans `test_material_properties.py`.

### Ajouter un onglet

1. `views/tabs/mon_tab.py` avec `create_mon_tab()` (pattern §5.3).
2. `main_window.py` : import, instanciation, entrée dans `all_tabs`, liste du menu *Onglets → Ouvrir*, tuple `_all_tabs` (pour `bind_controller`).
3. `views/styles.py` : icône dans `TAB_ICONS`.

### Ajouter un dialogue / assistant

Fonction `create_xxx_dialog(controller, parent=None)` dans `dialogs/`, appelée paresseusement depuis le menu ; passer par `controller.batch()` pour les créations multiples, et `controller.journal` pour tracer.

### Ajouter une préférence

Champ dans `Preferences` (valeur par défaut), widget dans `preferences_dialog` + ligne dans `apply_to`. `from_dict` ignore les clés inconnues (compatibilité ascendante).

### Ajouter un exemple

1. Fonction `ma_scene(project: Project) -> None` dans `lmgc90_core/scenes/demos.py` (entités uniquement, helpers de `_common.py`) ; l'enregistrer dans `SCENE_BUILDERS` et `scenes/__init__.py`.
2. Entrée `ExampleSpec(...)` dans `lmgc90_gui/examples/__init__.py` (import de la scène).
3. Documenter dans `examples.md`.

### Ajouter un générateur de masse (SoA)

Produire `centers (N, dim)` et `radii (N,)`, créer la population via `ParticlePopulation.create(...)`, puis `project.add(pop)` (ou `_insert_population`). Vérifier `POPULATION_TYPES`, l'émission `pre.py` et la matérialisation.

---

## 11. Tests

```bash
cd lmgc90_core   && python -m pytest -q     # headless : pureté, projet, population, io, validation
cd lmgc90_engine && python -m pytest -q     # sans pylmgc90 (stubs) ; marqueur « pylmgc » sinon
cd lmgc90_gui    && python -m pytest -q     # contrôleur headless ; certains tests Qt en QT_QPA_PLATFORM=offscreen
```

Tests structurants : `test_purity.py` (core), `test_engine_purity.py`, `test_wave1_scene.py` (parcours complet scène → export → save/load), `test_wave5_assistants.py` (maçonnerie, déformable), `test_visibility_suggestions.py`, `test_avatar_tab_generation.py` (Qt offscreen, `importorskip`).

---

## 12. Points de vigilance connus

Relevés à la lecture du code actuel (à confirmer / corriger) :

- **Persistance partielle** : `io.project_to_dict` n'enregistre que les avatars `origin == manual`. Les avatars issus de `apply_loop`, `apply_for_loop` ou **de la maçonnerie** (`expand_masonry` pose `origin=FACTORY`) ne sont donc pas relus à l'ouverture, alors que les groupes qui les référencent le sont. Les `for_loops` ne sont pas écrits dans le JSON.
- **Undo non uniforme** : `apply_for_loop`, `apply_masonry`, `deposit` (via `_insert_population`), ainsi que `remove_material/model/law/visibility/dof/postpro/population` et `update_*` du contrôleur modifient le `Project` sans `Command`. Le test `test_deposit_is_soa_and_one_undo` suppose pourtant un undo unique du dépôt.
- **Groupes et DOF dans `pre.py`** : `_emit_dof` pour une cible `group` n'applique l'opération qu'au premier membre (commentaire « apply to each member »). Le moteur (`_apply_dof`) boucle bien sur tous les membres.
- **Groupes de populations** : `EngineSession.run_granulo` ajoute aussi le `population_id` dans `avatar_groups` (doublon avec `population_groups`). `compute_script._resolve_group_ids` ne résout que les avatars AoS (index + 1) et ne gère pas les populations.
- **Émission des populations** : `pre_script._emit_population` ne connaît que disque, sphère, disque discret, cluster, cylindre ; polygone/polyèdre retombent sur `rigidDisk`.
- **Viewer** : `_render_via_pylmgc90` importe encore `...core.pylmgc_bridge` (ancienne architecture) ; le mode « 🔬 » doit être porté sur `EngineSession`.
- **Chargement de populations** : un sidecar absent ou incomplet ignore silencieusement les populations concernées (plus de `load_warnings`).
- **Non portés** : Particle Factory, convertisseur de script, assistants Projet/Granulométrie, onglet Templates/Bibliothèque.

---

## Annexe — Fichier à modifier selon le besoin

| Besoin | Fichier |
|---|---|
| Nouveau type de donnée / enum | `lmgc90_core/types.py`, `entities.py` |
| Règle de validation | `lmgc90_core/validate.py` |
| Nouvelle action annulable | `lmgc90_core/commands.py` + `Project` |
| Format de sauvegarde | `lmgc90_core/io.py` |
| Contenu de `pre.py` | `lmgc90_core/pre_script.py` |
| Contenu de `command.py` | `lmgc90_core/compute_script.py` |
| Appel pylmgc90 | `lmgc90_engine/avatar_factory.py`, `materialize.py` |
| DATBOX | `lmgc90_engine/datbox.py` |
| Logique GUI partagée | `lmgc90_gui/controller/project_controller.py` |
| Un onglet | `lmgc90_gui/views/tabs/<nom>_tab.py` |
| Vue 3D | `lmgc90_gui/views/viewer_3d.py` |
| Évaluation d'expressions | `lmgc90_gui/utils/safe_eval.py`, `eval_context.py` |
