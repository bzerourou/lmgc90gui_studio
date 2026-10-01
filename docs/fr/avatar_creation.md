# Créer et modifier un avatar

Un avatar est un corps de la scène. Il référence un matériau et un modèle, possède un centre et une couleur, puis des paramètres géométriques propres à son type. Créez d’abord le matériau et le modèle.

## Créer un avatar

1. Ouvrez **Onglets → Ouvrir → Avatars** (`Ctrl+3`).
2. Choisissez **Type**. Les types proposés sont adaptés à la dimension du projet.
3. Renseignez **Center X** et **Center Y**. En 3D, renseignez aussi **Center Z** ; ce champ est inactif en 2D.
4. Choisissez **Material** et **Model** dans les listes.
5. Renseignez **Color** avec le code de couleur LMGC90 souhaité (par exemple `BLUEx`, `REDxx` ou `GRAYx`).
6. Complétez **Type parameters**. Les champs changent automatiquement lorsque le type d’avatar change.
7. Cliquez sur **Add**. Une boîte d’avertissement précise les références manquantes ou paramètres invalides.
8. Actualisez le visualiseur 3D si vous souhaitez contrôler le placement.

## Types et paramètres géométriques

Les noms de paramètres sont ceux présentés dans **Type parameters**.

### Formes 2D

| Type | Paramètres spécifiques |
|---|---|
| `rigidDisk` | `r`, `is_Hollow` |
| `rigidDiscreteDisk` | `r` |
| `rigidJonc` | `axe1`, `axe2` |
| `rigidPolygon` | `generation_type`, `nb_vertices`, `radius`, `vertices` |
| `rigidOvoidPolygon` | `radius`, `vertices` |
| `rigidCluster` | `r`, `nb_disk` |
| `smoothWall` | `l`, `h`, `nb_polyg` |
| `roughWall`, `fineWall` | `l`, `r`, `nb_vertex` |
| `granuloRoughWall` | `l`, `rmin`, `rmax`, `nb_vertex` |

### Formes 3D

| Type | Paramètres spécifiques |
|---|---|
| `rigidSphere` | `r`, `is_Hollow` |
| `rigidCylinder` | `r`, `h`, `is_Hollow` |
| `rigidPlan` | `axe1`, `axe2`, `axe3` |
| `rigidPolyhedron` | `generation_type`, `nb_vertices`, `radius`, `vertices` |
| `roughWall3D` | `lx`, `ly`, `lz` |
| `granuloRoughWall3D` | `lx`, `ly`, `lz`, `rmin`, `rmax` |

`emptyAvatar` et `mesh` apparaissent également dans la liste. Leurs procédures sont détaillées dans [Avatar vide](empty_avatar.md) et [Corps déformable](meshed.md).

## Polygones et sommets personnalisés

Pour un polygone ou un polyèdre régulier, gardez `generation_type` à `regular`, puis renseignez le nombre de sommets et le rayon. Pour une géométrie explicite, saisissez les coordonnées dans **vertices**, séparées par des points-virgules :

```text
x1,y1; x2,y2; x3,y3
```

En 3D, chaque sommet doit contenir ses coordonnées `x,y,z`. Les sommets doivent former une géométrie valide et contenir au moins trois points en 2D ou quatre en 3D.

## Expressions et dimension

Les champs numériques de centre et plusieurs paramètres acceptent une valeur numérique ou une expression du projet. Par exemple, un rayon peut réutiliser une variable définie dans **Tools → Variables dynamiques…**. Une expression non résolue provoque un avertissement au moment de l’ajout.

En 2D, le centre contient deux coordonnées. En 3D, il en contient trois. Utilisez un modèle de la même dimension ; les types rigides doivent être associés à l’élément rigide de cette dimension (`Rxx2D` ou `Rxx3D`).

## Modifier un avatar

1. Sélectionnez la ligne de l’avatar dans la liste supérieure.
2. Les champs communs et les paramètres disponibles pour son type se rechargent.
3. Modifiez les valeurs nécessaires.
4. Cliquez sur **Update**.

## Supprimer un avatar

Sélectionnez l’avatar puis cliquez sur **Delete**. Vérifiez les groupes, conditions DOF et autres règles qui pouvaient le cibler. La suppression de l’avatar ne signifie pas nécessairement que toutes les références fonctionnelles du projet ont été réinterprétées.

## Couleur et contact

La couleur sert aussi à sélectionner des corps dans les tables **Visibility** et les opérations DOF ciblées par couleur. Gardez un code de couleur cohérent entre l’avatar, son contacteur et la table de visibilité. L’ajout de formes de contact supplémentaires est documenté dans [Contacteurs](contactors.md).
