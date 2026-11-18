# Architecture et guide de contribution

Ce dépôt contient trois paquets Python installables : `lmgc90_core`,
`lmgc90_engine` et `lmgc90_gui`. Les répertoires de paquets font autorité ;
ce guide décrit le code actuel, et non l'ancienne architecture monolithique
de l'interface.

## Frontières entre paquets

```text
lmgc90_gui  ─────►  lmgc90_engine  ─────►  lmgc90_core
     │                                       ▲
     └───────────────────────────────────────┘
```

| Paquet | Responsabilité |
|---|---|
| `lmgc90_core` | Entités de projet sérialisables, validation, commandes undo/redo, E/S du projet, constructeurs de scènes et génération de scripts. Il ne dépend ni de Qt ni de pylmgc90. |
| `lmgc90_engine` | Matérialise un `Project` core en objets pylmgc90, écrit les fichiers DATBOX et fournit les catalogues de compatibilité runtime. La dépendance pylmgc90 est optionnelle. |
| `lmgc90_gui` | Application PyQt6, vues, dialogues, contrôleur, workers et métadonnées GUI de la bibliothèque d'exemples. Qt et les dépendances de visualisation sont des extras optionnels. |

Les dépendances doivent rester orientées vers le core : celui-ci doit pouvoir
être utilisé sans le moteur ni l'interface. Les règles métier et les données
persistantes appartiennent au core ; la conversion spécifique au runtime
appartient au moteur ; les widgets appartiennent à l'interface.

## Arborescence du dépôt

```text
lmgc90_core/
  src/lmgc90_core/       # entités, Project, commandes, validation, E/S, scripts, scènes
  tests/
  examples/
lmgc90_engine/
  src/lmgc90_engine/     # EngineSession, matérialisation, DATBOX, catalogues
  tests/
lmgc90_gui/
  src/lmgc90_gui/
    controller/          # ProjectController et compatibilité des signaux
    views/                # fenêtre principale, onglets, widgets, viewer 3D
    dialogs/
    workers/
    examples/             # métadonnées ExampleSpec
  tests/
docs/
  en/
  fr/
```

Chaque paquet possède son propre `pyproject.toml`, son arborescence source et
ses tests. Le projet racine ne remplace pas les manifestes des paquets.

## Modèle core et persistance

`lmgc90_core.Project` est l'agrégat du projet. Les entités et fabriques sont
définies dans `entities.py` et `pre.py` ; `types.py` contient les enums et
schémas de repli ; `validate.py` contient la validation ; `commands.py`
implémente les mutations annulables.

Utilisez les méthodes publiques du projet, telles que `Project.add`,
`Project.deposit`, `Project.group` et les méthodes correspondantes de
modification/suppression. Les méthodes `Project._insert_*` et
`Project._drop_*` sont des API internes utilisées par `commands.py`, pas des
méthodes de mutation destinées à l'application.

`Avatar` et `ParticlePopulation` ont des identifiants stables (`avatar_id` et
`population_id`). N'utilisez pas la position dans une liste comme identité
persistante. Le champ `target_kind` d'un `ForLoop` détermine s'il génère des
avatars ou des populations ; il n'existe pas de drapeau `use_soa`.

Les fichiers projet utilisent l'extension `.lmgc90` et contiennent du JSON.
Lorsque des populations de particules sont présentes, leurs tableaux sont
stockés dans un sidecar voisin `.populations.npz`, référencé par le fichier
projet. Utilisez `Project.save` et `Project.load` (ou les fonctions
correspondantes de `io.py`) afin de garder les métadonnées et les tableaux
synchronisés.

Modules core utiles :

| Module | Responsabilité |
|---|---|
| `project.py`, `commands.py` | API du projet et undo/redo |
| `entities.py`, `types.py` | Entités persistantes, enums, schémas de repli |
| `validate.py` | Validation core |
| `generate.py`, `population.py`, `masonry.py` | Génération de boucles, populations et maçonnerie |
| `io.py` | JSON du projet et sidecar des populations |
| `pre_script.py`, `chipy_script.py`, `compute_script.py`, `pipeline.py` | Scripts solveur et scripts batch générés |
| `scenes/` | Constructeurs de scènes d'exemple sans dépendance GUI |

## Moteur

`lmgc90_engine.EngineSession` possède l'état runtime associé à un `Project`
core. `materialize.py` convertit les entités core en objets pylmgc90 et
conserve les correspondances entre identifiants du projet et corps runtime.
`datbox.py` gère l'écriture DATBOX ; `avatar_factory.py` construit les corps
runtime ; `schema/` fournit les catalogues de compatibilité runtime pour les
matériaux, lois et contacteurs.

Le moteur constitue la frontière pour le comportement spécifique à
pylmgc90. Ne placez pas d'objets pylmgc90 dans les entités core ou l'état GUI.
La génération de scripts et l'édition de projets ne doivent pas exiger
l'installation de pylmgc90.

## Interface et contrôleur

`lmgc90_gui.controller.ProjectController` est la façade GUI autour de
`Project` et `EngineSession`. Les vues lisent `controller.project` et
transmettent les mutations par les méthodes du contrôleur. Elles s'abonnent à
`state_changed` pour se rafraîchir ; les onglets ne doivent pas posséder la
logique métier ni des objets pylmgc90 runtime.

`views/main_window.py` assemble les registres actuels des onglets et menus.
Les fabriques d'onglets se trouvent dans `views/tabs/` ; les dialogues,
workers et vues spécifiques ont leurs propres répertoires. Les registres du
code font autorité : évitez de maintenir une seconde liste figée dans ce
guide.

Le point d'entrée de l'application est `lmgc90_gui.app.main` ; il ouvre la
fenêtre principale maximisée. Gardez les chemins de modules de diagnostic dans
les infobulles ou le journal de l'application plutôt que dans les libellés
visibles, car ceux-ci augmentent la largeur minimale de la fenêtre. La barre
d'outils du visualiseur 3D est répartie sur deux rangées et la barre des
résultats conserve une largeur minimale bornée afin que la fenêtre puisse
tenir sur un écran de bureau standard.

## Scènes d'exemple

Les constructeurs de scènes core sont des fonctions recevant un `Project`
et construisant une scène à partir d'entités et d'outils core. Ils sont
rassemblés dans `lmgc90_core.scenes.SCENE_BUILDERS`. Les entrées GUI
`ExampleSpec` contiennent les métadonnées d'affichage et référencent ces
mêmes fonctions ; l'interface vérifie la correspondance avec le registre des
scènes.

L'interface de chargement appelle `ProjectController.apply_scene`. Le
remplacement crée d'abord un nouveau projet ; l'ajout exige la même dimension
et préserve le projet ainsi que son historique. `apply_scene` traite les
configurations granulométriques en attente lors de l'application de la scène.

Pour ajouter un exemple :

1. Implémentez la scène dans `lmgc90_core/scenes/` avec les API core.
2. Exportez-la depuis `lmgc90_core.scenes` et enregistrez son ID dans
   `SCENE_BUILDERS`.
3. Ajoutez un `ExampleSpec` pour cet ID dans `lmgc90_gui/examples/`.
4. Mettez à jour les tests ciblés de scènes/export et la documentation
   utilisateur si nécessaire.

La liste GUI `EXAMPLES` est le catalogue visible actuel ; évitez d'en recopier
l'inventaire complet dans une documentation qui deviendrait immédiatement
obsolète.

## Catalogues dépendants du runtime

Les enums et schémas core fournissent des données de repli portables.
Lorsqu'elles sont disponibles, les données de compatibilité du moteur
proviennent d'un snapshot pylmgc90 versionné ou de l'introspection runtime ;
les formulaires GUI utilisent ces données et se replient sur le core si elles
manquent. Dans une documentation de catalogue, précisez la source et la
version décrites au lieu de présenter une liste runtime comme universelle.

## Tests et contribution

Chaque paquet possède sa suite pytest. Depuis le répertoire du paquet
concerné, lancez :

```text
python -m pytest
```

Modifiez la couche qui possède le comportement. Pour une nouvelle entité ou
règle de validation, commencez dans le core ; pour une conversion pylmgc90,
mettez à jour la matérialisation du moteur ; pour un widget, modifiez
l'interface et appelez l'API du contrôleur. Ajoutez des tests ciblés pour les
nouveaux comportements et préservez les frontières d'import et de dépendances
des paquets.
