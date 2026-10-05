# Boucles géométriques d’avatars

L’onglet **Loops** clone un avatar modèle et répartit ses copies selon une géométrie régulière. Ces boucles sont distinctes des boucles paramétriques multi-cibles de l’onglet [ForLoop](for_loop.md).

![](../captures/loops.png)

## Préparer le modèle

1. Créez un avatar dans **Avatars** avec son matériau, son modèle, sa couleur et ses paramètres géométriques.
2. Vérifiez sa position initiale : elle sert de base au clonage.
3. Ouvrez **Onglets → Ouvrir → Loops** (`Ctrl+4`).

## Définir la génération

1. Choisissez **Type** : `circle`, `grid`, `line` ou `spiral`.
2. Choisissez **Template avatar**.
3. Définissez **Count**, le nombre de copies à créer.
4. Renseignez les champs adaptés au motif :
   - `circle` : **Radius** détermine le rayon de placement ; utilisez également les offsets pour déplacer le centre de la disposition ;
   - `grid` : **Step** définit l’espacement ; les offsets déplacent la grille ;
   - `line` : **Step** définit l’espacement ; **Invert axis (line)** inverse l’orientation de la ligne ;
   - `spiral` : **Radius** et **Spiral factor** déterminent l’ouverture et la progression, avec les offsets de position.
5. En 3D, renseignez les offsets X, Y et Z nécessaires ; en 2D, l’offset Z n’a pas d’effet géométrique.
6. Renseignez **Group** pour enregistrer les avatars générés dans un groupe.
7. Cliquez sur **Apply loop**.
8. Lisez la confirmation du nombre de corps créés et vérifiez le résultat dans **Avatars** ou le visualiseur 3D après **Rafraîchir la scène**.

## Supprimer une boucle

Sélectionnez la boucle dans la liste, puis cliquez sur **Delete selected loop** et confirmez. La boucle et les avatars qu’elle a générés sont retirés ; les autres avatars du projet restent en place. Cette action peut être annulée ou rétablie avec les commandes **Undo** et **Redo**.

## Résultat et répétition

Chaque copie est ajoutée au projet comme un avatar indépendant. Appliquer de nouveau une boucle ajoute une nouvelle série ; cela ne remplace pas la génération précédente. Donnez un nom de groupe distinct si vous devez distinguer plusieurs séries.

Les boucles géométriques ne modifient pas directement les propriétés physiques du modèle. Pour faire varier matériaux, modèles, DOF, visibilité ou paramètres granulométriques avec une expression d’itération, utilisez **ForLoop**.
