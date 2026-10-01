# Découverte de l’interface

LMGC90_GUI organise la création d’une scène dans des onglets et menus. Les libellés visibles sont actuellement majoritairement en anglais ; les termes entre guillemets ci-dessous correspondent aux commandes de l’application.

## Fenêtre principale

![Vue de l’interface](../captures/interface_sections.png)

La fenêtre rassemble :

1. la barre de menus en haut ;
2. une barre d’outils avec les actions fréquentes ;
3. les onglets de travail au centre ;
4. **Model tree** à gauche, qui résume les objets du projet ;
5. **History** à droite, qui retrace les actions ;
6. la barre d’état, avec le projet, la dimension, le nombre de corps et la disponibilité de pylmgc90.

La palette de commandes est accessible par **Help → Palette de commandes…** ou `Ctrl+K`.

## Fichier et projet

| Action | Raccourci | Fonction |
|---|---|---|
| **File → New** | `Ctrl+N` | Choisir la dimension 2D/3D et le nom d’un nouveau projet. |
| **File → Open…** | `Ctrl+O` | Ouvrir un projet `.lmgc90`. |
| **File → Save** | `Ctrl+S` | Enregistrer le projet à son emplacement courant. |
| **File → Save As…** | `Ctrl+Shift+S` | Enregistrer une copie ou définir l’emplacement. |
| **Project → Set dimension…** | — | Changer la dimension ; les modèles existants peuvent devenir incompatibles. |
| **Edit → Undo / Redo** | `Ctrl+Z` / `Ctrl+Y` | Annuler ou rétablir les actions disponibles dans l’historique. |

Pour une procédure détaillée, voir [Créer et organiser un projet](project_wizard.md).

## Menus principaux

### Tools

Le menu **Tools** donne accès aux exports `pre.py` et `command.py`, à l’export complet, au pipeline local/SLURM, aux assistants Mesh et Maçonnerie, aux variables dynamiques, à `pre.visuAvatars` et aux préférences.

- **Assistant Mesh déformable…** : `Ctrl+Shift+D`.
- **Assistant Maçonnerie…** : `Ctrl+Shift+M`.
- **Variables dynamiques…** : `Ctrl+V`.
- **Preferences…** : `Ctrl+,`.

Les anciens assistants généraux de projet et de granulométrie ne figurent plus dans cette version.

### Computation

- **Generate DATBOX / scripts…** : `Ctrl+F5`.
- **Run computation** : `F5`. Cette action ouvre l’onglet **Compute** et déclenche le lancement du calcul ; **Compute** n’est pas une entrée de **Onglets → Ouvrir** dans la version actuelle.
- **Application journal** : `F7`.

L’onglet **Compute** expose les paramètres et le journal du calcul ; voir [Préparer et lancer un calcul](calculs.md).

### Onglets

Le menu **Onglets → Ouvrir** donne accès aux onglets de création. Les neuf premiers raccourcis sont :

| Raccourci | Onglet |
|---|---|
| `Ctrl+1` | Materials |
| `Ctrl+2` | Models |
| `Ctrl+3` | Avatars |
| `Ctrl+4` | Loops |
| `Ctrl+5` | ForLoop |
| `Ctrl+6` | Granulo |
| `Ctrl+7` | Contact |
| `Ctrl+8` | Visibility |
| `Ctrl+9` | DOF |

Les onglets additionnels comprennent **Post-pro**, **Visualisation 3D**, **Groups**, **Contactors**, **Deformable** et **Masonry**. **Compute** est ouvert par l’action **F5**. Les onglets **Materials** et **Models** sont essentiels et ne peuvent pas être fermés. **Onglets → Onglets par défaut** (`Ctrl+Alt+D`) restaure la disposition initiale.

### Exemples et aide

- **Exemples → Bibliothèque d’exemples…** (`Ctrl+Shift+E`) ouvre le catalogue de scènes.
- **Help → Palette de commandes…** (`Ctrl+K`) filtre les commandes ; tapez pour rechercher, utilisez les flèches et appuyez sur Entrée pour exécuter.
- **Help → About / shortcuts** affiche la version et les raccourcis.

## Model tree et History

**Model tree** reflète le contenu du projet et se rafraîchit après les opérations : matériaux, modèles, avatars, populations, groupes, lois, visibilité et DOF. C’est un panneau de consultation, pas l’éditeur principal ; utilisez les onglets concernés pour modifier un objet.

**History** conserve l’historique des actions de la session. La barre d’état affiche aussi le nombre de corps et de variables dynamiques.

## Barre d’outils

La barre principale donne accès notamment à **New**, **Open**, **Save**, au lancement du calcul, à la préparation DATBOX/scripts, aux variables dynamiques et à la palette de commandes.

## Préférences

Ouvrez **Tools → Preferences…** (`Ctrl+,`) pour régler notamment les dossiers de projet/travail, paramètres de calcul, confirmation d’exécution et comportement de sauvegarde disponibles dans cette version.

Pour apprendre les opérations spécifiques, consultez les chapitres de [l’index français](overview.md).
