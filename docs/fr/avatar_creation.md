# Créer et modifier un avatar

Un avatar est un corps de la scène. Il référence un matériau et un modèle, possède un centre et une couleur, puis des paramètres géométriques propres à son type. Créez d’abord le matériau et le modèle.

![](../captures/avatars.png)

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
| `roughWall` | Mur rugueux | `l`, `r`, `nb_vertex` |
| `fineWall` | Mur fin | `l`, `r`, `nb_vertex` |
| `smoothWall` | Mur lisse | `l`, `h`, `nb_polyg` |
| `granuloRoughWall` | Mur granulaire | `l`, `rmin`, `rmax`, `nb_vertex` |


### Formes 3D

| Type | Paramètres spécifiques |
|---|---|
| `rigidSphere` | `r`, `is_Hollow` |
| `rigidCylinder` | `r`, `h`, `is_Hollow` |
| `rigidPlan` | `axe1`, `axe2`, `axe3` |
| `rigidPolyhedron` | `generation_type`, `nb_vertices`, `radius`, `vertices` |
| `roughWall3D` | `lx`, `ly`, `lz` |
| `granuloRoughWall3D` | `lx`, `ly`, `lz`, `rmin`, `rmax` |

`emptyAvatar` et `mesh` apparaissent également dans la liste. Leurs procédures sont détaillées dans [Avatar vide](empty_avatar.md) et [Corps déformable](empty_avatar.md#avatar-mesh) ou [Assistant des déformables](meshed.md).


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

Exemples de couleurs que vous pourriez utiliser : 

| Code | Couleur |
|------|---------|
| `BLUEx` | Bleu |
| `REDxx` | Rouge |
| `VERTx` | Vert |
| `JAUNx` | Jaune |
| `GRAYx` | Gris |
| `BLACx` | Noir |
| `WHITx` | Blanc |
| `ORANx` | Orange |
| `CYANx` | Cyan |
| `MAGEx` | Magenta |
| `VIOLx` | Violet |
| `ROSEx` | Rose |

## Types d'avatars 2D

### 1. rigidDisk — Disque rigide 2D

Corps circulaire rigide 2D. C'est le type le plus courant pour les simulations granulaires.

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `r` (rayon) | Rayon du disque (m). | `0.1` |
| `is_hollow` | Si coché, crée un disque creux (`is_Hollow=True`). Utile pour les anneaux rigides. | case à cocher |

---

### rigidJonc — Jonc / Ellipse rigide 2D

Corps elliptique rigide 2D. Défini par deux demi-axes.

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `axe1` | Demi-axe principal (m) — longueur. | `0.15` |
| `axe2` | Demi-axe secondaire (m) — largeur. | `0.05` |


---

### rigidPolygon — Polygone rigide 2D

Corps polygonal rigide 2D. Trois modes de génération disponibles selon `generation_type`.

| Paramètre | Description | Valeurs |
|-----------|-------------|---------|
| `generation_type` | Mode de génération de la forme. | `regular` · `full` · `bevel` |
| `nb_vertices` | Nombre de sommets (pour `regular` et `full`). | `3` à `20` |
| `radius` | Rayon du cercle circonscrit (m) — utilisé pour `regular`. Non utilisé pour `full` et `bevel`. | `0.1` |
| `vertices` | Liste explicite de sommets `[[x1,y1],[x2,y2],…]` — utilisé pour `full` et `bevel`. | `[[-0.1,-0.1],[0.1,-0.1],[0.,0.1]]` |

**Modes de génération :**

- **`regular`** : polygone régulier (tous les côtés égaux). Défini par `nb_vertices` et `radius` (rayon du cercle circonscrit).
- **`full`** : polygone quelconque à partir d'une liste de sommets explicites. Le rayon n'est pas utilisé.
- **`bevel`** : polygone avec chanfreinage automatique des angles pour éviter les singularités de contact.

---

### rigidOvoidPolygon — Ovoïde rigide 2D

Corps ovoïde (ellipse polygonale) rigide 2D. Approximation polygonale d'une ellipse.

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `ra` | Demi-axe principal (m). | `0.15` |
| `rb` | Demi-axe secondaire (m). | `0.08` |
| `nb_vertices` | Nombre de sommets de l'approximation polygonale. | `20` |

---

### rigidDiscreteDisk — Disque discret rigide 2D

Corps circulaire rigide 2D à cinématique discrète. Même géométrie qu'un `rigidDisk`, mais avec un contacteur de type `xKSID` (disque discret). Utilisé dans certains modèles discrets avancés.

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `r` (rayon) | Rayon du disque (m). | `0.1` |

---

### rigidCluster — Cluster de disques rigides 2D

Corps rigide 2D composé de plusieurs disques liés rigidement. Permet de créer des formes non convexes complexes.

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `r` | Rayon de chaque disque dans le cluster (m). | `0.05` |
| `nb_vertices` (nb_disk) | Nombre de disques dans le cluster. | `4` |

> Le paramètre est nommé `nb_disk` dans le script pylmgc90 généré (pas `nb_vertices`).

---

### roughWall — Mur rugueux 2D

Paroi 2D rugueuse composée de disques alignés. Utilisé pour les parois confinantes avec rugosité géométrique.

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `l` | Longueur totale du mur (m). | `2.0` |
| `r` | Rayon des disques constituant la rugosité (m). | `0.05` |
| `nb_vertex` | Nombre de disques le long du mur. Défaut : `10`. | `20` |

---

### fineWall — Mur fin 2D

Paroi 2D fine composée de disques très petits. Mêmes paramètres que `roughWall` mais avec une rugosité plus fine.

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `l` | Longueur totale du mur (m). | `2.0` |
| `r` | Rayon des disques (m). Typiquement très petit (0,001 à 0,01). | `0.005` |
| `nb_vertex` | Nombre de disques. Défaut : `10`. | `50` |

---

### smoothWall — Mur lisse 2D

Paroi 2D lisse définie par une demi-largeur et une hauteur. Contacteur `CLxxx` (surface continue).

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `l` | Demi-longueur du mur (m) — la longueur totale est `2 × l`. | `1.0` |
| `h` | Demi-hauteur (épaisseur) du mur (m). | `0.01` |
| `nb_polyg` | Nombre de segments polygonaux. Défaut : `10`. | `20` |

---

### granuloRoughWall — Mur granulaire rugueux 2D

Paroi 2D avec rugosité aléatoire générée par distribution granulométrique de disques.

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `l` | Longueur totale du mur (m). | `2.0` |
| `rmin` | Rayon minimal des disques (m). | `0.01` |
| `rmax` | Rayon maximal des disques (m). | `0.05` |
| `nb_vertex` | Nombre de disques. Défaut : `10`. | `30` |

---

## Types d'avatars 3D

### rigidSphere — Sphère rigide 3D

Corps sphérique rigide 3D. Équivalent 3D du `rigidDisk`.

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `r` (rayon) | Rayon de la sphère (m). | `0.1` |
| `is_hollow` | Si coché, crée une Sphère creuse (`is_Hollow=True`).  | case à cocher |

---

### rigidPlan — Plan rigide 3D

Surface plane rigide 3D. Défini par trois vecteurs directeurs formant un repère local.

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `axe1` | Vecteur du premier axe du plan (direction X locale). | `[1.0, 0.0, 0.0]` |
| `axe2` | Vecteur du deuxième axe du plan (direction Y locale). | `[0.0, 1.0, 0.0]` |
| `axe3` | Normale au plan (direction Z locale). | `[0.0, 0.0, 1.0]` |

> Les trois vecteurs doivent former une base orthonormée directe.

---

### rigidCylinder — Cylindre rigide 3D

Corps cylindrique rigide 3D.

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `r` (rayon) | Rayon du cylindre (m). | `0.1` |
| `h` | Hauteur (longueur axiale) du cylindre (m). Défaut : `1.0` si absent. | `0.5` |
| `is_hollow` | Si coché, crée un cylindre creux (`is_Hollow=True`).  | case à cocher |

---

### rigidPolyhedron — Polyèdre rigide 3D

Corps polyédrique rigide 3D. Deux modes de génération disponibles selon `generation_type`.

| Paramètre | Description | Valeurs |
|-----------|-------------|---------|
| `generation_type` | Mode de génération. | `regular` · `vertices` |
| `nb_vertices` | Nombre de sommets (pour `regular`). | `8` (cube), `12` (icosaèdre)… |
| `radius` | Rayon du polyèdre régulier (m) — pour `regular`. | `0.1` |
| `vertices` | Liste explicite de sommets 3D `[[x,y,z],…]` — pour `vertices`. | `[[−1,−1,−1],[1,−1,−1],…]` |
| `faces` | Connectivité des faces `[[i,j,k],…]` (dans `wall_params`) — pour `vertices`. | `[[0,1,2],[2,3,0],…]` |

**Modes de génération :**

- **`regular`** : polyèdre régulier (similaire à une sphère polygonale). Défini par `nb_vertices` et `radius`.
- **`vertices`** : polyèdre quelconque défini par une liste explicite de sommets et la connectivité des faces.

---

### roughWall3D — Mur rugueux 3D

Paroi 3D rugueuse composée de sphères alignées sur une surface rectangulaire.

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `lx` | Dimension du mur en X (m). | `2.0` |
| `ly` | Dimension du mur en Y (m). | `2.0` |
| `r` | Rayon des sphères de rugosité (m). | `0.05` |

---

### granuloRoughWall3D — Mur granulaire rugueux 3D

Paroi 3D rugueuse avec sphères de tailles aléatoires.

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `lx` | Dimension en X (m). | `2.0` |
| `ly` | Dimension en Y (m). | `2.0` |
| `rmin` | Rayon minimal des sphères (m). | `0.01` |
| `rmax` | Rayon maximal des sphères (m). | `0.05` |

