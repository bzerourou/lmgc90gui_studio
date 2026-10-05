# Génération paramétrique avec ForLoop

L’onglet **ForLoop** répète une opération à partir d’une plage de valeurs et d’expressions. Contrairement à **Loops**, qui place des clones d’avatars selon une forme géométrique, ForLoop accepte différentes cibles : avatars, matériaux, modèles, opérations DOF, tables de visibilité, dépôts granulométriques ou distributions de rayons.

![](../captures/for_loops.png)

## Préparer la boucle

1. Créez les objets de base dont la cible dépend. Par exemple, une boucle d’avatars nécessite un avatar modèle ; une boucle de matériaux nécessite un matériau existant.
2. Ouvrez **Onglets → Ouvrir → ForLoop**.
3. Choisissez **Cible de la boucle**.
4. Renseignez **Variable**. Le nom `i` est proposé par défaut ; les expressions du formulaire peuvent employer cette variable.
5. Saisissez **start**, **stop (exclu)** et **step**.
6. Sélectionnez **Template** lorsque le type de cible le demande.
7. Complétez seulement les expressions correspondant à la cible. Les champs non concernés sont désactivés.
8. Cliquez sur **Appliquer la boucle**. L’application affiche le nombre d’éléments produits ou un message indiquant la valeur invalide.

`stop` est exclu. Avec `start=0`, `stop=5` et `step=1`, la variable parcourt `0, 1, 2, 3, 4` : cinq répétitions.

## Supprimer une boucle

Sélectionnez la boucle dans la liste, puis cliquez sur **Supprimer la boucle sélectionnée** et confirmez. La boucle et les éléments qu’elle a générés sont supprimés, sans toucher aux autres objets du projet. La suppression peut être annulée ou rétablie avec **Undo** et **Redo**.

## Cibles et expressions

| Cible | Modèle requis | Champs variables proposés |
|---|---|---|
| `avatar` | Avatar modèle | `expr X`, `expr Y`, `expr Z`, `expr rayon` |
| `material` | Matériau modèle | `expr densité (matériau)` |
| `model` | Modèle modèle | Copie du modèle sélectionné selon la plage |
| `dof` | Opération DOF existante | Paramètres de l’opération sélectionnée |
| `visibility` | See-table existante | `expr alert (see)` |
| `granulo` | Configuration granulométrique, ou paramètres de l’onglet Granulo | `expr N`, `expr rmin`, `expr rmax` |
| `granulo_dist` | Configuration granulométrique, ou valeurs par défaut | `expr N`, `expr rmin`, `expr rmax` |

Les champs utilisent des expressions numériques sûres. Une série peut par exemple placer des avatars avec `expr X = i * 0.1` et `expr Y = 0.0`. Dans le cas d’un avatar, choisissez également un **Groupe** pour rassembler les créations si nécessaire.

## Exemples de réglage

### Rangée d’avatars

1. Choisissez la cible `avatar`.
2. Sélectionnez l’avatar à cloner dans **Template**.
3. Réglez `start=0`, `stop=10`, `step=1`.
4. Saisissez `i * 0.2` pour `expr X`, `0.0` pour `expr Y`, et `0.0` pour `expr Z` en 3D.
5. Donnez un nom de groupe, par exemple `ligne1`.
6. Cliquez sur **Appliquer la boucle** et vérifiez que 10 avatars ont été créés.

### Série de matériaux à densité variable

1. Choisissez la cible `material` et un matériau modèle.
2. Définissez la plage d’itération.
3. Saisissez une expression de densité telle que `2500 + 100*i`.
4. Appliquez la boucle et contrôlez les noms et densités dans **Materials**.

### Distribution de rayons

1. Choisissez `granulo_dist` pour produire une distribution seule, ou `granulo` pour créer une population.
2. Réglez la plage et les expressions du nombre de particules et des rayons.
3. Appliquez la boucle ; vérifiez le résultat dans **Granulo** et dans le visualiseur après actualisation.

## Contrôles et précautions

- Vérifiez que `step` n’est pas nul et que le sens de la plage est cohérent.
- `stop` étant exclu, vérifiez le nombre d’itérations avant une génération volumineuse.
- Des expressions dépendant de `i` doivent produire des valeurs valides pour chaque itération.
- L’application ajoute les résultats au projet ; une nouvelle exécution ne remplace pas les créations précédentes.
- Une cible qui dépend d’un template ne peut pas être appliquée si aucun élément approprié n’est sélectionné.

Pour les arrangements strictement géométriques (cercle, grille, ligne, spirale), voir [Boucles géométriques](loops.md).
