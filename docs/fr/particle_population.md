# Populations de particules (SoA) et granulométrie

Une **population de particules** (`ParticlePopulation`) est la façon dont LMGC90_GUI stocke **un grand nombre de grains identiques** (même type, même matériau, même modèle, même couleur) : au lieu de créer un avatar par grain, le projet garde deux tableaux (positions, rayons). C'est ce qui permet de manipuler des dizaines de milliers de grains sans ralentir l'interface.

- **Partie A — Utilisateur** : créer, contrôler, visualiser, sauvegarder et supprimer une population ; relier les grains au contact ; dépannage.
- **Partie B — Développeur** : modèle de données, génération, persistance, consommateurs, extension.

> **Changements par rapport à l'ancienne version**
> - Le SoA n'est plus une **case à cocher** : un dépôt crée **toujours** une population (sauf « Distribution seule »).
> - L'assistant de granulométrie par étapes et le dialogue « numpy bêta » n'existent plus : tout passe par l'onglet **Granulo** (`Ctrl+6`).
> - La génération par défaut est un **tirage aléatoire sans chevauchement** (numpy), pas un dépôt gravitaire ; le dépôt « physique » `pre.depositIn*` n'est utilisé que si pylmgc90 est disponible (voir §A.4).
> - Les boucles d'avatars (**Loops**, **ForLoop** cible `avatar`) restent des avatars individuels : elles ne créent pas de population.

---

# Partie A — Utilisateur

## A.1 Population ou avatars individuels ?

| Besoin | Outil | Résultat |
|---|---|---|
| Des centaines à des centaines de milliers de grains de même type | **Granulo** | 1 population |
| Quelques corps à éditer un par un (murs, pièces, formes variées) | **Avatars**, **Loops**, **ForLoop (avatar)**, **Masonry** | 1 avatar par corps |
| Corps composites, maillages | **Avatars (emptyAvatar)** + **Contactors**, **Deformable** | avatars |

Ce que vous **pouvez** faire avec une population : la visualiser, la relier aux lois de contact (par **couleur** et **forme**), la sauvegarder, l'exporter vers `pre.py` / DATBOX, la supprimer en bloc.

Ce que vous **ne pouvez pas** faire : modifier un grain isolé, le déplacer, le supprimer, le cibler seul avec une opération DOF, ou l'utiliser dans `avatar[i]` / `group['nom']` des expressions. Pour changer quoi que ce soit, supprimez la population et recréez-la.

## A.2 Pré-requis

1. Un **matériau** (type `RIGID`, densité par exemple 2500) — onglet *Materials*.
2. Un **modèle rigide** de la dimension du projet (`MECAx` / `Rxx2D` ou `Rxx3D`) — onglet *Models*.
3. Idéalement, les **parois** du conteneur (murs, sol) et leurs conditions aux limites, ainsi qu'une **loi de contact**.

## A.3 Le formulaire de l'onglet Granulo

Ouvrez **Onglets → Ouvrir → Granulo** (`Ctrl+6`).

| Champ | Détail | Défaut |
|---|---|---|
| **N particules** | de 1 à 500 000 | `200` |
| **Rayon min / max** | 10⁻⁶ à 10³ ; **min doit être strictement inférieur à max** | `0.05` / `0.15` |
| **Conteneur** | liste filtrée par la dimension du projet (tableau ci-dessous) | 1ᵉʳ de la liste |
| *Paramètres du conteneur* | champs qui changent avec le conteneur | voir tableau |
| **Type d'avatar** | 2D : `rigidDisk`, `rigidDiscreteDisk`, `rigidPolygon` ; 3D : `rigidSphere`, `rigidPolyhedron` | 1ᵉʳ de la liste |
| **Matériau** | tous les matériaux du projet | — |
| **Modèle** | modèles de la **même dimension** que le projet | — |
| **Couleur (5 car.)** | complétée par des `x` si plus courte (ex. `BLU` → `BLUxx`), tronquée à 5 | `BLUEx` |
| **Groupe (5 car.)** | idem | `granx` |
| **Seed** | entier ≥ 0, ou `random` (valeur minimale du champ) | `42` |
| **Utiliser dépôt pylmgc (engine)** | voir §A.4 | décoché |
| **Distribution seule (rayons)** | ne crée ni avatars ni population | décoché |

> **Types `rigidPolygon` / `rigidPolyhedron`.** Ils sont proposés dans la liste mais le formulaire ne permet pas encore de renseigner leurs paramètres (nombre de sommets) : le dépôt est alors refusé avec un message du type *« rigidPolygon: extra_params['nb_vertices'] … »*. Utilisez pour l'instant `rigidDisk`, `rigidDiscreteDisk` ou `rigidSphere`.

### Conteneurs

| Dim. | Conteneur | Paramètres (défaut) | Zone de dépôt |
|---|---|---|---|
| 2D | **Box2D** | `lx=1`, `ly=1` | rectangle `[0, lx] × [0, ly]` |
| 2D | **Disk2D** | `r=1` | disque de rayon `r` centré en `(0, 0)` |
| 2D | **Drum2D** | `r=1` | idem Disk2D (tambour) |
| 2D | **Couette2D** | `rint=0.5`, `rext=1` | anneau entre `rint` et `rext`, centré en `(0, 0)` |
| 3D | **Box3D** | `lx=ly=lz=1` | parallélépipède `[0, lx] × [0, ly] × [0, lz]` |
| 3D | **Sphere3D** | `r=1` | sphère centrée en `(0, 0, 0)` |
| 3D | **Cylinder3D** | `r=1`, `lz=2` | cylindre d'axe Z, base en `z=0`, centré en `x=y=0` |

Les grains sont placés **entièrement à l'intérieur** du conteneur (le rayon est pris en compte). Le conteneur est une **zone de tirage**, pas un corps : il ne crée aucune paroi. Placez vos murs et votre sol en conséquence (ils doivent entourer la zone indiquée, d'où les coordonnées de paroi du type `x = −épaisseur` et `x = lx + épaisseur` dans les exemples).

Un conteneur d'une autre dimension que le projet est refusé (*« Conteneur Box3D est 3D, projet en 2D »*).

## A.4 Choisir le mode de génération

Quatre comportements possibles :

| Mode | Comment | Particularités |
|---|---|---|
| **Numpy (par défaut sans pylmgc90)** | cases décochées, pylmgc90 absent | **tirage aléatoire sans chevauchement** ; reproductible avec `Seed` ; aucune gravité |
| **pylmgc90 (si installé)** | automatique, **même case décochée** | utilise les routines `pre.depositInBox2D/3D`, `…Drum2D`, `…Couette2D`, `…Sphere3D`, `…Cylinder3D` ; en cas d'échec, repli silencieux sur numpy (message dans le journal `F7`) |
| **pylmgc90 forcé** | case **Utiliser dépôt pylmgc (engine)** cochée | pas de repli : si pylmgc90 n'est pas disponible ou échoue, un message d'erreur s'affiche |
| **Distribution seule** | case **Distribution seule (rayons)** | tire N rayons dans `[rmin, rmax]`, enregistre l'intention (`[dist]` dans la liste) ; **aucun** grain, aucune population ; la case pylmgc est alors désactivée |

> Les positions obtenues avec numpy et avec pylmgc90 diffèrent (algorithmes différents). Pour des études comparables, gardez le même mode et la même graine.

## A.5 Générer, contrôler, supprimer

1. Vérifiez matériau, modèle, rayons, conteneur, couleur et groupe.
2. **Générer le dépôt**.
3. Un message indique : *« Population pop_xxx… — N particules (Conteneur) »*. **N est le nombre réellement placé**, qui peut être inférieur au nombre demandé (§A.6).
4. La liste du haut affiche la population : `[SoA] xxxxxxxx…  N=…  <type>  <groupe>`. Les distributions seules apparaissent sous la forme `[dist] N=… r∈[…,…] → … rayons (Conteneur)`.
5. **Supprimer sélection** supprime la population sélectionnée en bloc (ainsi que son intention de dépôt). Cette suppression n'est pas annulable par `Ctrl+Z`. Les lignes `[dist]` ne se suppriment pas depuis cette liste.
6. Dans **Visualisation 3D**, cliquez **Rafraîchir la scène** pour afficher les grains.
7. La barre d'état affiche `bodies=` = avatars + grains.
8. Le **Model tree** liste la population (identifiant abrégé, nombre de grains, type).

## A.6 Combien de grains seront réellement placés ?

Le tirage numpy tente des candidats par lots et s'arrête au bout de **25 × N** essais : si le conteneur est trop petit ou trop plein, il y a moins de grains que demandé (aucune erreur n'est levée).

Ordres de grandeur (empilement aléatoire sans gravité) :

| Dimension | Fraction de surface/volume occupée raisonnablement atteignable |
|---|---|
| 2D (disques) | environ 40 à 50 % |
| 3D (sphères) | environ 25 à 35 % |

Estimation rapide en 2D : `N × π × r_moyen² ÷ (lx × ly)` doit rester sous ≈ 0,4. Pour obtenir des assemblages plus compacts, utilisez une polydispersité plus large (`rmax/rmin ≥ 2`), un conteneur plus grand, ou le dépôt pylmgc90 (gravitaire) puis un calcul de compaction.

**Volumes** : le dépôt numpy compare chaque lot aux grains déjà placés ; son coût croît vite avec N. Pour plusieurs dizaines de milliers de grains, prévoyez un temps et une mémoire importants (ou préférez pylmgc90, ou plusieurs dépôts de taille moyenne).

## A.7 Plusieurs dépôts

Chaque dépôt est **indépendant** : aucune vérification de chevauchement entre populations. Deux dépôts dans le même conteneur (même zone) produiront des grains qui se recouvrent. Pour des populations côte à côte, utilisez des conteneurs aux zones disjointes (par exemple un `Box2D` pour l'une, un `Disk2D` ou une autre géométrie pour l'autre) ou déplacez les parois en conséquence. Donnez des **couleurs différentes** à chaque population si elles doivent avoir des lois de contact différentes.

## A.8 Reproductibilité

- Même graine + mêmes paramètres + même mode ⇒ mêmes rayons et mêmes positions (mode numpy).
- `random` (valeur minimale du champ Seed) = graine aléatoire : chaque exécution diffère.
- Les positions sont enregistrées dans le projet : rouvrir un projet **ne redépose pas** les grains.

## A.9 Relier la population au contact

Les grains sont des corps rigides `RBDY2`/`RBDY3` avec un contacteur `DISKx` (2D) ou `SPHER` (3D) de la **couleur** de la population.

1. **Contact** : créez une loi (par exemple `IQS_CLB`, frottement 0,3–0,5).
2. **Visibility** : bouton **⚡ Grains↔grains** (grain/grain) et **⚡ Grains↔sol** (grain/paroi `JONCx`). L'onglet propose automatiquement la couleur et le contacteur de la population. Vérifiez la loi et **Alert**, puis ajoutez.
3. **Murs** : `smoothWall` / `roughWall` (contacteur `JONCx`) ou `rigidPlan` (3D, `PLANx`), couleur différente de celle des grains, et **fixés** par `imposeDrivenDof` (`component=[1, 2, 3]`, `dofty='vlocy'`, `ct=0.0`).
4. **Compute** : détecteurs adaptés (`DKDKx` + `DKJCx` en 2D ; `SPSPx` + `SPPLx`… en 3D).
5. Bouton **⚠ Vérifier** de *Visibility* pour repérer une couleur de population sans table.

Rappels :
- Un **groupe de population** (champ *Groupe* du formulaire) n'est pas, dans la version actuelle, une cible proposée par les onglets **DOF** et **Post-pro** (ils listent les groupes d'avatars).
- Une opération DOF ne peut pas cibler un grain isolé.
- La cible DOF « color » n'est pas appliquée lors de l'écriture directe de la DATBOX par le moteur (vérifier le `pre.py` exporté si vous en dépendez).

## A.10 Boucle `ForLoop` et populations

Dans **ForLoop**, deux cibles utilisent les dépôts :

| Cible | Effet |
|---|---|
| `granulo` | une **population** par itération |
| `granulo_dist` | une **distribution de rayons** par itération (sans grain) |

À chaque itération : graine = valeur arrondie de la variable ; `expr N`, `expr rmin`, `expr rmax` (champs ForLoop) remplacent respectivement le nombre de particules et les rayons. Tous les autres paramètres (conteneur, matériau, modèle, type, couleur) sont repris du **premier dépôt déjà présent dans le projet**, ou à défaut de valeurs par défaut (premier matériau/modèle, `Box2D` 1×1 en 2D ou `Box3D` 1×1×1 en 3D). Les itérations sont indépendantes : voir §A.7 pour les chevauchements.

## A.11 Sauvegarde, export, performances

### Fichiers

| Fichier | Contenu |
|---|---|
| `mon_projet.lmgc90` | JSON : métadonnées de la population (identifiant, type, matériau, modèle, couleur, origine, dimension, groupe, `n_particles`), intention de dépôt (`granulo_generations`) |
| `mon_projet.populations.npz` | tableaux compressés `centres` et `rayons` de toutes les populations |

**Copiez, déplacez ou archivez les deux fichiers ensemble.** Si le `.npz` manque à l'ouverture, les populations concernées sont ignorées sans message : le projet s'ouvre sans grains. Si le projet n'a plus de population, l'ancien `.npz` est supprimé à la sauvegarde.

Poids typique des tableaux : `(dimension + 1) × 8` octets par grain avant compression, soit 24 octets en 2D (≈ 2,4 Mo pour 100 000 grains).

### Exports

- **`pre.py`** : chaque population devient une boucle qui recrée les corps à partir de tableaux numpy **écrits en clair** dans le fichier. Pour de très grosses populations, le fichier est volumineux ; la DATBOX écrite directement (Computation → Generate DATBOX, pylmgc90 requis) évite cette étape.
- **`command.py`** : identique avec ou sans population (les grains sont des corps comme les autres dans la DATBOX).

### Performances

- Viewer 3D : le rendu transforme chaque grain en objet temporaire puis fusionne les disques/sphères par lot de même couleur. C'est supportable jusqu'à quelques dizaines de milliers de grains ; au-delà, l'actualisation devient lente (le viewer est une aide de contrôle).
- Les grains d'une même couleur sont dessinés comme un **seul** objet : ils ne sont pas sélectionnables individuellement en mode *Sélect.*.
- Création des corps pylmgc90 : un appel par grain (limite de LMGC90), donc temps proportionnel à N à l'écriture de la DATBOX.

## A.12 Exemples fournis

| Exemple (Exemples → Bibliothèque) | Dépôt |
|---|---|
| Dépôt granulométrique | 500 disques, `Box2D` 4 × 4, rayons 0,03–0,08, graine 42 |
| Tambour rotatif | 200 disques, `Drum2D` `r=2.0`, rayons 0,05–0,09 |
| Décharge en trémie | 180 disques, `Box2D` 2 × 1,6, rayons 0,04–0,07 |
| Avalanche sur pente | 200 disques, `Box2D` 1,5 × 1,0 |
| Compression biaxiale | 200 disques, `Box2D` 2 × 1,5 |
| Cellule de Couette | 250 disques, `Couette2D` `rint=1`, `rext=2` |
| Cylindre 3D (dépôt) | 1000 sphères, `Cylinder3D` `R=7,5`, `lz=10` |
| Tambour/Lit granulaire… | voir le catalogue |

Chargez-en un avec **Remplacer**, puis utilisez **Rafraîchir la scène**. Les grains sont déposés automatiquement au chargement de l'exemple.

## A.13 Dépannage

| Symptôme | Cause / solution |
|---|---|
| *rmin doit être < rmax* | rayon min ≥ rayon max |
| *Matériau et modèle requis* | créer un matériau et un modèle de la dimension du projet |
| *Conteneur … est 2D/3D, projet en …* | choisir un conteneur de la bonne dimension (ou changer la dimension du projet) |
| Population plus petite que demandée | conteneur trop plein (§A.6) |
| Erreur à `rigidPolygon` / `rigidPolyhedron` | paramètres de sommets non renseignables dans le formulaire (§A.3) |
| *pylmgc90 is required…* | case pylmgc forcée sans pylmgc90 : décochez-la |
| Rien n'apparaît en 3D | cliquer **Rafraîchir la scène** ; vérifier que la population existe dans la liste |
| Les grains traversent le sol | pas de loi/visibilité pour la couleur des grains ; sol non fixé ; détecteur non activé |
| Grains superposés après deux dépôts | dépôts indépendants dans la même zone (§A.7) |
| Population disparue à la réouverture | fichier `.populations.npz` absent ou renommé |
| Impossible de supprimer une ligne `[dist]` | non prévu depuis cette liste |
| Ctrl+Z n'annule pas le dépôt | la suppression/annulation d'un dépôt se fait via **Supprimer sélection** |

---

# Partie B — Développeur

> Code : `lmgc90_core/population.py`, `io.py`, `generate.py`, `project.py`, `commands.py`, `pre_script.py` · `lmgc90_engine/granulo.py`, `avatar_factory.py`, `materialize.py` · `lmgc90_gui/views/tabs/granulo_tab.py`, `for_loop_tab.py`, `controller/project_controller.py`.

## B.1 AoS vs SoA

| Critère | AoS — `Avatar` | SoA — `ParticlePopulation` |
|---|---|---|
| Stockage | un objet par corps dans `project.avatars` | 2 tableaux contigus + méta dans `project.populations` |
| Identité | `avatar_id` stocké | `population_id` stocké ; id de particule dérivé `"{pop_id}:{i}"` |
| Création | `Project.add` (une commande par avatar), boucles, maçonnerie | `Project.deposit` / engine `run_granulo` |
| Édition individuelle | native | non (bloc) |
| Types | tous | `types.POPULATION_TYPES` |
| Sérialisation | JSON (avatars `origin == manual`) | méta JSON + sidecar `.npz` |
| `pre.py` | une ligne par avatar | une boucle par population |
| `safe_eval` | `avatar[i]`, `group[...]` | non exposé |

```
Project
├── avatars:           list[Avatar]
├── populations:       list[ParticlePopulation]
├── population_groups: dict[str, list[population_id]]
└── granulo:           list[GranuloConfig]     # intentions de dépôt
```

## B.2 Modèle de données

```python
@dataclass
class ParticlePopulation:
    population_id: str          # "pop_<uuid>"
    avatar_type: AvatarType     # homogène
    material_name: str
    model_name: str
    color: str
    origin: AvatarOrigin
    dimension: int              # = centers.shape[1]
    centers: np.ndarray         # (N, dim) float64
    radii: np.ndarray           # (N,)     float64
    group_name: Optional[str] = None
    extra_params: dict = {}
```

`POPULATION_TYPES` : `RIGID_DISK`, `RIGID_SPHERE`, `RIGID_DISCRETE`, `RIGID_CLUSTER`, `RIGID_CYLINDER`, `RIGID_POLYGON`, `RIGID_POLYHEDRON`.

`extra_params` exigés (`_validate_extra`) :

| Type | Clé |
|---|---|
| `rigidCluster` | `nb_disk` (int ≥ 2, défaut 3) |
| `rigidCylinder` | `h` > 0 (obligatoire) |
| `rigidPolygon` | `nb_vertices` (int ≥ 3) |
| `rigidPolyhedron` | `nb_vertices` (int ≥ 4) |

> `GranuloTab` et `NumpyGranulo.deposit` n'alimentent pas `extra_params` ; polygones/polyèdres échouent donc à `create()` (voir A.3).

### Construction validée

```python
ParticlePopulation.create(
    avatar_type="rigidDisk", material_name="TDURx", model_name="rigid",
    centers=centers, radii=radii, color="BLUEx", origin="granulo",
    group_name="depot", population_id=None, extra_params=None,
)
```

`ValueError` si : type non supporté, `centers` ≠ `(N, 2|3)`, `radii` ≠ `(N,)`, longueurs différentes, un rayon ≤ 0, `extra_params` invalides.

### Identité et vues

```python
pop.particle_avatar_id(i)     # "pop_xxx:42"
parse_particle_id("pop_xxx:42")  # ("pop_xxx", 42)   (ids.py)
pop.as_avatar_view(i)         # UN Avatar temporaire (id dérivé)
pop.bounds(); pop.radius_stats(); len(pop)
```

`as_avatar_view` ne doit pas être appelé en boucle hors cas assumé (viewer).

## B.3 Génération

### Cœur : `NumpyGranulo` (`generate.py`)

```python
NumpyGranulo().deposit(config) -> GranuloResult(population, nb_requested, nb_placed, attempts)
```

- `rng = np.random.default_rng(config.seed)` ; lots de `min(512, 4 × restant)` candidats ; rayons uniformes dans `[radius_min, radius_max]` ;
- filtre `_inside` (conteneur, rayon inclus), puis `_no_hit_batch` contre toutes les particules déjà placées, puis contrôle séquentiel `_no_hit_one` ;
- plafond `max_attempts = N × 25` ; l'objet est créé avec `ParticlePopulation.create(...)`, `origin=GRANULO`, `config.population_id` renseigné ;
- coût : comparaison dense `(lot × placées)` ⇒ mémoire/temps élevés pour N très grand.

Conteneurs : `Box2D` (`[0,lx]×[0,ly]`), `Disk2D`/`Drum2D` (`r`), `Couette2D` (`rint`,`rext`), `Box3D`, `Sphere3D`, `Cylinder3D` (`r`/`R`, `lz`).

### `Project.deposit(config)`

```python
if not config.create_avatars:       # distribution seule
    radii = rng.uniform(rmin, rmax, N) ; config.radii = [...] ; self.granulo.append(config) ; return None
result = NumpyGranulo().deposit(config)
self._insert_population(result.population, config)   # (voir dev.md §12 pour l'historique)
return result.population
```

`_insert_population` ajoute la population, rattache `config` à `project.granulo` (avec `population_id`) et renseigne `population_groups[group_name]`.

### Moteur (`lmgc90_engine/granulo.py`)

`deposit_population(config, ...)` : tire les rayons (`default_rng(seed)`), appelle `pre.depositInBox2D(radii, lx, ly)`, `depositInBox3D`, `depositInDrum2D`/`Disk2D`, `depositInCouette2D`, `depositInSphere3D`, `depositInCylinder3D`, normalise les coordonnées (`_normalize_coords`, `_parse_result`) et renvoie une population. `EngineSession.run_granulo(config)` l'ajoute à `project` via `project.add(pop)` (et alimente `population_groups` ; elle ajoute aussi l'id dans `avatar_groups`, voir dev.md §12).

### Contrôleur

```
controller.deposit(config)
  ├─ create_avatars=False → Project.deposit
  ├─ pylmgc dispo         → session.run_granulo ; échec → journal.warning + NumpyGranulo
  └─ sinon                → Project.deposit
controller.run_granulo_pylmgc(config, **kw)   # forcé, pas de repli
controller.remove_population(pid)             # _drop_population direct
```

### `ForLoop` (`Project.apply_for_loop`)

Cibles `granulo` / `granulo_dist` : base = `self.granulo[0]` (ou valeurs par défaut) ; `expressions` : `nb_particles`|`n`, `radius_min`|`rmin`, `radius_max`|`rmax` (évaluées par `_safe_arith`) ; `seed=int(round(i))` ; `group_name = for_loop.group_name` ; `create_avatars = (kind == "granulo")` ; chaque itération appelle `self.deposit(cfg)`.

## B.4 Persistance (`io.py`)

```python
sidecar_path_for("p.lmgc90")            # p.populations.npz  (with_suffix("").with_suffix(".populations.npz"))
save_populations_sidecar(pops, npz)     # clés "<pid>__centers", "<pid>__radii" ; vide ⇒ supprime l'ancien .npz
load_populations_sidecar(npz)           # {pid: (centers, radii)} ; absent ⇒ {}
```

- `project_to_dict` écrit `particle_populations` (méta via `to_meta_dict()`), `populations_groups`, `granulo_generations` (incluant `radii` pour les distributions seules) et, si des populations existent, `particle_populations_sidecar`.
- `load_project` fusionne méta + tableaux ; une population dont les tableaux sont introuvables est ignorée (pas d'avertissement). Les `history` sont restaurés par `load_stacks`.
- Formes : `to_meta_dict()` / `from_meta_and_arrays()` (production), `to_dict()` / `from_dict()` (autonome).

## B.5 Consommateurs

| Consommateur | Comportement |
|---|---|
| `pre_script._emit_population` | `centers_<id>` / `radii_<id>` en clair + boucle `pre.<fn>(r=…, center=…, model=…, material=…, color=…)` ; `fn` ∈ {`rigidDisk`, `rigidSphere`, `rigidDiscreteDisk`, `rigidCluster`, `rigidCylinder`} (autres types ⇒ `rigidDisk`) |
| `engine.materialize` | `build_population_bodies` (un appel `pre.<fn>` par particule) ; `scene.bodies_by_population_id[pid]` ; `session.population_map` ; populations ajoutées après les avatars AoS |
| `viewer_3d` | `_expand_renderables` : `as_avatar_view(i)` pour chaque particule ; fusion par `(type, couleur)` pour disque/sphère ; acteur fusionné non « pickable » |
| `scene_geometry` | sous-échantillonnage à `max_population_preview = 5000` |
| `visibility_tab` | `_project_contact_options` ajoute `(corps, forme, couleur, rôle)` d'après `pop.avatar_type`, `pop.dimension`, `pop.color` |
| `dof_tab` | liste les couleurs de populations ; groupes = `avatar_groups` |
| `compute_script` | indifférent ; `_resolve_group_ids` ne résout que les avatars AoS |
| `eval_context` | `avatar[i]`, `group[...]` : AoS uniquement |

## B.6 Historique

`AddPopulation(population, config)` est la commande d'ajout (`revert` ⇒ `_drop_population`). `Project.add(ParticlePopulation)` l'emploie. Vérifier dans le code courant si `Project.deposit` passe bien par `_run(AddPopulation)` (le test `test_deposit_is_soa_and_one_undo` l'attend ; l'implémentation lue appelle `_insert_population` directement). Voir [dev.md §12](dev.md#12-points-de-vigilance-connus).

## B.7 Étendre

**Nouveau type SoA** : `types.POPULATION_TYPES` → `population._validate_extra` (+ `as_avatar_view`) → `avatar_factory.build_population_bodies` (`fn_map`) → `pre_script._emit_population` (`fn`) → GUI (`GranuloTab` : champs pour `extra_params`) → tests.

**Corriger polygone/polyèdre en GUI** : ajouter dans `GranuloTab` des champs `nb_vertices`/`radius` et les passer à `GranuloConfig` (`extra_params` à introduire dans le modèle), puis à `NumpyGranulo.deposit` → `ParticlePopulation.create(extra_params=…)`.

**Nouveau conteneur** : `NumpyGranulo._sample` + `_inside`, `granulo_tab._CONTAINERS`, éventuellement `engine.granulo._call_deposit`.

**Checklist**
- [ ] création via `ParticlePopulation.create`
- [ ] insertion via `Project.add(pop)` ou `deposit` (idéalement commande annulable)
- [ ] `population_groups` renseigné
- [ ] émission `pre.py` et matérialisation gèrent le type
- [ ] viewer et aperçu 2D gèrent le type
- [ ] tests : `create`, `to_dict/from_dict`, `to_meta_dict` + aller-retour sidecar, dépôt déterministe (`seed`)

## B.8 Fichiers concernés

| Fichier | Rôle |
|---|---|
| `lmgc90_core/population.py` | dataclass SoA, validation, vues, sérialisation |
| `lmgc90_core/io.py` | sidecar `.npz`, save/load |
| `lmgc90_core/generate.py` | `NumpyGranulo`, `GranuloResult` |
| `lmgc90_core/project.py`, `commands.py` | `deposit`, `AddPopulation`, `_insert/_drop_population`, `apply_for_loop` |
| `lmgc90_core/pre_script.py` | `_emit_population` |
| `lmgc90_core/scenes/demos.py` | scènes avec `GranuloConfig` |
| `lmgc90_engine/granulo.py` | dépôt pylmgc90 |
| `lmgc90_engine/avatar_factory.py`, `materialize.py` | corps pylmgc90 |
| `lmgc90_gui/views/tabs/granulo_tab.py`, `for_loop_tab.py` | formulaires |
| `lmgc90_gui/controller/project_controller.py` | `deposit`, `run_granulo_pylmgc`, `remove_population`, `apply_scene` |
| `lmgc90_gui/views/viewer_3d.py`, `utils/scene_geometry.py` | rendu |