# Granulométrie et populations de particules

L’onglet **Granulo** génère une population de particules dont les rayons sont compris entre deux bornes, et les place dans un conteneur. Une population SoA permet de représenter de nombreux grains sans créer une ligne graphique individuelle pour chaque particule.

![](../captures/granulo.png)

## Préparer le projet

1. Créez un matériau compatible avec les grains dans **Materials**.
2. Créez un modèle rigide adapté à la dimension (`MECAx` avec `Rxx2D` ou `Rxx3D`) dans **Models**.
3. Ouvrez **Onglets → Ouvrir → Granulo** (`Ctrl+6`).

## Régler le dépôt

1. Indiquez **N particules**.
2. Renseignez **Rayon min** et **Rayon max**. Le rayon minimum doit être strictement inférieur au maximum.
3. Choisissez le **Conteneur** proposé pour la dimension du projet :
   - 2D : `Box2D`, `Disk2D`, `Drum2D`, `Couette2D` ;
   - 3D : `Box3D`, `Sphere3D`, `Cylinder3D`.
4. Complétez les dimensions du conteneur affichées sous **Conteneur** : `lx`, `ly`, `lz`, `r`, `rint` ou `rext` selon le cas.
5. Choisissez le **Type d’avatar**. En 2D : disque, disque discret ou polygone ; en 3D : sphère ou polyèdre.
6. Sélectionnez **Matériau** et **Modèle**.
7. Renseignez **Couleur (5 car.)** et **Groupe (5 car.)**.
8. Réglez **Seed** pour reproduire le tirage. La valeur `random` demande une graine aléatoire.

## Choisir un mode de génération

- **Dépôt NumPy SoA** : laissez **Utiliser dépôt pylmgc (engine) si disponible** décoché. L’application construit une population compacte et l’ajoute au projet.
- **Dépôt pylmgc** : cochez cette option si pylmgc90 est disponible dans l’environnement et que vous souhaitez utiliser ses routines de dépôt.
- **Distribution seule** : cochez **Distribution seule (rayons)** pour générer et enregistrer les rayons sans produire d’avatars ni de population. Dans ce mode, le dépôt pylmgc est désactivé.

## Générer et contrôler le résultat

1. Relisez le nombre, les rayons, le conteneur, le type de corps et les références matériau/modèle.
2. Cliquez sur **Générer le dépôt**.
3. Vérifiez le message de confirmation.
4. La liste présente les populations créées sous la forme `[SoA]` avec leur effectif, leur type et leur groupe. Les distributions seules sont repérées par `[dist]`.
5. Pour retirer une population, sélectionnez-la dans la liste puis cliquez sur **Supprimer sélection**.
6. Ouvrez **Visualisation 3D** et cliquez sur **Rafraîchir la scène** pour voir la population.

La suppression proposée concerne une population ; vérifiez la ligne sélectionnée avant de valider.

## Dimension et contact

Le type de conteneur doit correspondre à la dimension du projet. Les populations génèrent leurs propres corps rigides/couleurs, mais les interactions nécessitent encore des lois et des tables de visibilité compatibles. Dans **Visibility**, utilisez les couleurs et contacteurs proposés depuis la population ; choisissez la bonne paire candidat/antagoniste et une distance **Alert** cohérente.

Pour répéter une génération avec une variable d’itération, consultez [ForLoop](for_loop.md). Pour comprendre la représentation des grandes populations, voir [Populations de particules](particle_population.md) (référence technique).


# ParticlePopulation — Architecture SoA des particules de masse

> Complément au [guide développeur](dev.md). Référence technique (pas un guide d'utilisation graphique).
> Code : `lmgc90_core/population.py`, `lmgc90_core/io.py`, `lmgc90_core/generate.py`, `lmgc90_engine/granulo.py`, `lmgc90_engine/avatar_factory.py`.

---

## 1. Pourquoi SoA ?

| Approche | Structure | Cas d'usage | Limite pratique |
|---|---|---|---|
| **AoS** (`project.avatars`) | Un objet `Avatar` par corps | Murs, avatars manuels, déformables, édition unitaire | quelques milliers avant ralentissement de l'UI |
| **SoA** (`project.populations`) | Un `ParticlePopulation` = deux tableaux numpy | Dépôts granulométriques, grands volumes homogènes | dizaines à centaines de milliers de particules |

`ParticlePopulation` **ne remplace pas** `Avatar` : les deux coexistent dans `Project`.

```
Project
├── avatars:      list[Avatar]               # AoS — édition fine
└── populations:  list[ParticlePopulation]   # SoA — volumes
    population_groups: dict[nom → [population_id]]
```

**Changement majeur par rapport à l'ancienne version** : le SoA n'est plus une option à cocher. `Project.deposit()` produit **toujours** une population (sauf mode « distribution seule »). Il n'y a plus de `particle_populations` dans un `ProjectState`, ni de `_pylmgc_population_bodies` dans le contrôleur.

---

## 2. Modèle de données

```python
@dataclass
class ParticlePopulation:
    population_id: str             # "pop_<uuid>" — un id par population
    avatar_type: AvatarType        # homogène
    material_name: str             # homogène
    model_name: str                # homogène
    color: str                     # homogène
    origin: AvatarOrigin           # GRANULO, LOOP, ...
    dimension: int                 # 2 ou 3 (= centers.shape[1])
    centers: np.ndarray            # (N, dim) float64
    radii: np.ndarray              # (N,)     float64
    group_name: Optional[str] = None
    extra_params: dict = {}        # nb_disk, h, nb_vertices, ...
```

### 2.1 Types supportés

`types.POPULATION_TYPES` : `RIGID_DISK`, `RIGID_SPHERE`, `RIGID_DISCRETE`, `RIGID_CLUSTER`, `RIGID_CYLINDER`, `RIGID_POLYGON`, `RIGID_POLYHEDRON`.

`extra_params` requis selon le type (validés dans `_validate_extra`) :

| Type | `extra_params` |
|---|---|
| `rigidCluster` | `nb_disk` entier ≥ 2 (défaut 3) |
| `rigidCylinder` | `h` > 0 obligatoire |
| `rigidPolygon` | `nb_vertices` entier ≥ 3 |
| `rigidPolyhedron` | `nb_vertices` entier ≥ 4 |

### 2.2 Construction validée

Toujours via `create()` :

```python
pop = ParticlePopulation.create(
    avatar_type="rigidDisk",              # AvatarType ou chaîne
    material_name="TDURx", model_name="rigid",
    centers=centers, radii=radii,
    color="BLUEx",
    origin="granulo",
    group_name="depot",
    population_id=None,                   # généré si absent
    extra_params=None,
)
```

Erreurs `ValueError` : type non supporté, `centers` pas `(N, 2|3)`, `radii` pas `(N,)`, longueurs différentes, rayon ≤ 0, `extra_params` invalides.

### 2.3 Identité des particules

Dérivée, jamais stockée (`ids.py`) :

```python
pop.particle_avatar_id(i)                   # "pop_abc…:42"
parse_particle_id("pop_abc…:42")            # ("pop_abc…", 42)
```

Le `population_id` est stable ; l'indice `i` est positionnel (la population est traitée comme un bloc : pas de suppression ou de réordonnancement individuel).

### 2.4 Vue ponctuelle

```python
av = pop.as_avatar_view(i)    # construit UN Avatar (avatar_id = id dérivé)
```

À réserver à l'inspection ponctuelle. Ne **jamais** boucler sur toute la population hors cas assumé (le viewer 3D le fait, voir §6).

### 2.5 Statistiques

```python
len(pop); pop.bounds(); pop.radius_stats()   # {"min","max","mean"}
```

---

## 3. Génération

### 3.1 Cœur : `NumpyGranulo`

`Project.deposit(config)` appelle `NumpyGranulo().deposit(config)` (rejet par lots vectorisés, `seed` reproductible) puis insère la population. Conteneurs gérés :

| Dim. | `container_type` | `container_params` |
|---|---|---|
| 2D | `Box2D` | `lx`, `ly` — domaine `[0, lx] × [0, ly]` (comme `depositInBox2D`) |
| 2D | `Disk2D`, `Drum2D` | `r` |
| 2D | `Couette2D` | `rint`, `rext` |
| 3D | `Box3D` | `lx`, `ly`, `lz` |
| 3D | `Sphere3D` | `r` |
| 3D | `Cylinder3D` | `r` (ou `R`), `lz` |

Le résultat (`GranuloResult`) donne `nb_placed`, `nb_requested`, `fill_ratio`. Le nombre placé peut être inférieur au nombre demandé.

### 3.2 Mode « distribution seule »

`GranuloConfig(create_avatars=False)` : tire seulement `nb_particles` rayons dans `[radius_min, radius_max]`, les stocke dans `config.radii` et ajoute le config à `project.granulo`. Aucune population, aucun avatar.

### 3.3 Dépôt pylmgc90 (moteur)

`lmgc90_engine.granulo.deposit_population(config)` appelle `pre.depositInBox2D/3D`, `depositInDrum2D/Disk2D`, `depositInCouette2D`, `depositInSphere3D`, `depositInCylinder3D` et renvoie une `ParticlePopulation`. Le contrôleur choisit :

```
controller.deposit(config)
  ├─ create_avatars=False → Project.deposit (rayons seuls)
  ├─ pylmgc dispo         → session.run_granulo (repli sur NumpyGranulo en cas d'échec)
  └─ sinon                → Project.deposit (NumpyGranulo)
```

L'onglet **Granulo** expose aussi une case explicite « dépôt pylmgc (engine) » (`run_granulo_pylmgc`).

### 3.4 Scènes et `ForLoop`

- Les scènes d'exemple déclarent un `GranuloConfig` dans `project.granulo` ; `ProjectController.apply_scene` appelle ensuite `deposit` pour chaque config sans `population_id`.
- `ForLoop` cible `granulo` → une population par itération ; cible `granulo_dist` → distributions de rayons seules. La cible `avatar` d'un `ForLoop` reste **AoS** (pas de chemin SoA pour les boucles d'avatars).

---

## 4. Persistance à deux niveaux

### 4.1 Sidecar `.npz`

| Fichier | Contenu |
|---|---|
| `projet.lmgc90` (JSON) | `particle_populations` : métadonnées via `to_meta_dict()` (sans tableaux, avec `n_particles`), `populations_groups`, `granulo_generations`, clé `particle_populations_sidecar` |
| `projet.populations.npz` | `"<population_id>__centers"` et `"<population_id>__radii"` (compressé) |

```python
from lmgc90_core.io import sidecar_path_for, save_populations_sidecar, load_populations_sidecar

sidecar_path_for(Path("p.lmgc90"))        # → p.populations.npz
save_populations_sidecar(populations, npz_path)
load_populations_sidecar(npz_path)        # {pop_id: (centers, radii)}
```

Règles :
- aucune population → aucun `.npz` écrit ; un ancien sidecar est **supprimé** ;
- sidecar absent → `load_populations_sidecar` renvoie `{}`.

### 4.2 Rechargement

`io.load_project` fusionne méta JSON + tableaux ; seules les populations dont les tableaux sont trouvés sont restaurées (`if pid in arrays`). Une population dont le tableau manque est **ignorée silencieusement** (il n'y a plus de `load_warnings`).

### 4.3 Formes de sérialisation

| Méthodes | Usage |
|---|---|
| `to_meta_dict()` / `from_meta_and_arrays(meta, centers, radii)` | production (JSON + npz) |
| `to_dict()` / `from_dict(d)` | autonome (tableaux en listes) — tests, duplication |

---

## 5. Historique et undo

`AddPopulation(population, config)` est la `Command` d'ajout (une commande quelle que soit la taille), `revert` appelle `_drop_population` (retire population, `GranuloConfig` associé et entrées de `population_groups`). `Project.add(ParticlePopulation)` passe par cette commande. Voir [dev.md §12](dev.md#12-points-de-vigilance-connus) pour la couverture undo de `Project.deposit` et `controller.remove_population`.

---

## 6. Consommateurs de populations

| Consommateur | Comportement |
|---|---|
| **`pre_script.emit_pre`** | par population : `np.array` des centres/rayons, puis boucle `for … pre.rigidXxx(...)` + `bodies.addAvatar`. Fonctions émises : disque, sphère, disque discret, cluster, cylindre (les autres types retombent sur `rigidDisk`). |
| **`engine.materialize`** | `build_population_bodies` : une boucle `pre.<fn>` par particule ; résultat dans `scene.bodies_by_population_id[pop_id]` (et exposé par `session.population_map`). Les populations sont ajoutées **après** les avatars AoS dans le conteneur `bodies`. |
| **`viewer_3d`** | `_expand_renderables` appelle `as_avatar_view(i)` pour chaque particule (O(N) objets temporaires), puis fusionne par lots (type + couleur) disque/sphère. Gros volumes : prévoir la lenteur. |
| **`scene_geometry`** (schéma 2D) | sous-échantillonnage à `max_population_preview=5000` particules. |
| **`visibility_tab` / `dof_tab`** | utilisent `pop.color` et `pop.avatar_type` pour suggérer couleurs/contacteurs ; les DOF ciblent un avatar, un groupe d'avatars ou une couleur (pas une particule). |
| **`safe_eval`** | `avatar[...]` et `group[...]` n'exposent **que** `project.avatars` / `avatar_groups`. |
| **`compute_script`** | agnostique : une fois la DATBOX écrite, une particule SoA est un corps `RBDY2/3` comme les autres. Les groupes d'avatars ne résolvent que les AoS. |

---

## 7. Comparaison AoS / SoA

| Critère | AoS — `Avatar` | SoA — `ParticlePopulation` |
|---|---|---|
| Stockage | un objet par corps | 2 tableaux contigus + méta |
| Identité | `avatar_id` stocké | `population_id` stocké ; id de particule dérivé |
| Création | `Project.add` × N (une commande chacun) ; boucles/maçonnerie | `Project.deposit` — une population |
| Édition individuelle | native (`AvatarTab`) | non (population = bloc) |
| Types | tous | `POPULATION_TYPES` |
| Sérialisation | JSON inline (avatars `manual`) | méta JSON + sidecar `.npz` |
| `pre.py` | une ligne par avatar | une boucle par population |
| Undo | une commande par avatar | `AddPopulation` (une commande) |
| `safe_eval` | oui | non |

**Règle de choix** : grand nombre de particules strictement homogènes, sans besoin d'édition individuelle → SoA ; sinon AoS.

---

## 8. Pièges et conventions

1. **Homogénéité** : une population = un type, un matériau, un modèle, une couleur.
2. **Pas de matérialisation en masse** (`as_avatar_view` en boucle) hors viewer.
3. **Sidecar synchronisé** : le `.npz` est écrit avec le `.lmgc90` ; à copier/déplacer ensemble.
4. **Régénération** : redéposer crée une **nouvelle** population (nouvel `population_id`) ; les anciens ids `pop_xxx:i` deviennent invalides.
5. **Maçonnerie** : ce n'est pas du SoA — les briques restent des `Avatar` individuels.
6. **Nouveau type SoA** : ajouter le type à `POPULATION_TYPES`, valider ses `extra_params` (`_validate_extra`), compléter `build_population_bodies` (`fn_map`) et `pre_script._emit_population`.

---

## 9. Checklist contributeur

- [ ] Création uniquement via `ParticlePopulation.create`
- [ ] Insertion via `Project.add(pop)` / `Project.deposit` (commande annulable)
- [ ] `population_groups` mis à jour (fait par `_insert_population`)
- [ ] Sidecar : rien à faire si l'on passe par `Project.save`
- [ ] `pre_script`, `avatar_factory`, `viewer_3d` gèrent le nouveau type
- [ ] Tests : `create`, `to_dict/from_dict`, `to_meta_dict` + aller-retour sidecar, dépôt déterministe (`seed`)

---

## 10. Fichiers concernés

| Fichier | Rôle |
|---|---|
| `lmgc90_core/population.py` | dataclass SoA, validation, vues, sérialisation |
| `lmgc90_core/io.py` | sidecar `.populations.npz`, save/load projet |
| `lmgc90_core/generate.py` | `NumpyGranulo`, `GranuloResult` |
| `lmgc90_core/project.py`, `commands.py` | `deposit`, `AddPopulation`, `_insert/_drop_population` |
| `lmgc90_core/pre_script.py` | `_emit_population` |
| `lmgc90_engine/granulo.py` | dépôt pylmgc90 → population |
| `lmgc90_engine/avatar_factory.py`, `materialize.py` | corps pylmgc90 par particule |
| `lmgc90_gui/controller/project_controller.py` | `deposit`, `run_granulo_pylmgc`, `remove_population` |
| `lmgc90_gui/views/tabs/granulo_tab.py` | formulaire de dépôt |
| `lmgc90_gui/views/viewer_3d.py` | rendu (expansion O(N)) |
| `lmgc90_gui/utils/scene_geometry.py` | aperçu 2D sous-échantillonné |