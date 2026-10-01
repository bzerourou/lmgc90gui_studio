# Variables dynamiques

Les variables dynamiques enregistrent des expressions réutilisables dans les champs numériques de l’interface qui prennent en charge les expressions. Le dialogue affiche leur expression, leur valeur résolue et leur type.

## Ajouter une variable

1. Ouvrez **Tools → Variables dynamiques…** (`Ctrl+V`).
2. Saisissez un **Nom** constitué d’un identifiant valide, par exemple `r_min` ou `epaisseur` (sans espace et sans commencer par un chiffre).
3. Saisissez l’**Expression**, par exemple `0.05` ou `largeur + joint`.
4. Consultez **Aperçu**. Le dialogue indique la valeur obtenue ou l’erreur de résolution.
5. Cliquez sur **Add / Update**.
6. Vérifiez l’expression, la valeur et le type dans le tableau.

## Modifier, rafraîchir ou supprimer

- Cliquez une ligne du tableau pour charger le nom et l’expression dans le formulaire, puis cliquez **Add / Update** pour enregistrer la modification.
- Cliquez **Refresh** pour recalculer les valeurs affichées.
- Sélectionnez une ligne ou saisissez son nom, puis cliquez **Delete** pour supprimer la variable.
- Cliquez **Close** pour quitter le dialogue.

Les expressions sont évaluées dans l’ordre des variables du projet ; une expression peut s’appuyer sur une variable définie précédemment. Une référence inconnue ou circulaire déclenche une erreur de prévisualisation.

## Utiliser une variable dans la scène

1. Définissez la variable dans le dialogue.
2. Ouvrez un onglet qui accepte les expressions numériques, par exemple **Avatars**.
3. Saisissez le nom de la variable dans un champ numérique, par exemple dans un rayon ou une coordonnée.
4. Validez la création ou la modification et corrigez toute erreur signalée.

Exemples d’expressions :

| Expression | Utilisation possible |
|---|---|
| `0.05` | Rayon ou longueur fixe. |
| `diametre / 2` | Rayon dérivé d’une dimension définie auparavant. |
| `largeur + joint` | Distance composée de paramètres du projet. |

Le dialogue utilise un évaluateur restreint pour les expressions autorisées. Ce n’est pas un interpréteur Python général : ne comptez pas sur l’accès à tous les modules Python ou à toutes les méthodes d’objets.
