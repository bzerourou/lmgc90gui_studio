# Visualisation de la scène

LMGC90_GUI propose deux voies pour inspecter le modèle : le **visualiseur 3D intégré** (PyVista) et le visualiseur natif de pylmgc90 lancé avec **pre.visuAvatars**. Ces outils montrent la scène préparée ; ils ne remplacent pas un outil d’analyse des résultats de calcul.

![](../captures/viewer_3d.png)

## Ouvrir et actualiser le visualiseur intégré

1. Ouvrez **Onglets → Ouvrir → Visualisation 3D**.
2. Vérifiez que le projet contient des avatars ou une population.
3. Cliquez sur **Rafraîchir la scène**. Le transfert vers le viewer est manuel : après une modification du projet, relancez cette action.
4. L’indicateur de la barre du viewer signale si la scène affichée doit être actualisée et indique le nombre d’objets envoyé.

Le viewer intégré requiert les modules `pyvista` et `pyvistaqt`. Si l’un manque, le panneau affiche un message d’indisponibilité au lieu de la scène.

## Naviguer dans la scène

- **Nav.** : mode caméra. Faites glisser le bouton gauche pour orbiter, utilisez la molette pour zoomer et le bouton droit pour déplacer la caméra.
- **XY**, **XZ**, **Iso** : vues prédéfinies. La vue `XY` convient généralement aux projets 2D. La vue `YZ` n’est pas proposée dans cette version.
- **🔄 Réinitialiser la caméra** : rétablit le cadrage initial.
- **Arêtes** : affiche ou masque les arêtes des géométries.
- **Curseur d’opacité** : rend les avatars plus ou moins transparents.
- **🗑️ Effacer** : retire les objets de la vue courante. Cliquez à nouveau sur **Rafraîchir la scène** pour repeupler le viewer depuis le projet.

## Sélectionner et mesurer

1. Cliquez sur **Sélect.**.
2. Cliquez sur un avatar dans la scène. Il est mis en évidence et ses informations sont indiquées dans la barre d’état.
3. Pour mesurer une distance, cliquez sur **Règle**.
4. Cliquez une première fois sur un point de la scène (A), puis sur le second point (B). La distance est affichée par le viewer.
5. Revenez au mode **Nav.** pour reprendre la navigation.

La sélection porte sur les objets représentés par le visualiseur. En cas de scène vide ou d’objets trop petits à l’écran, réinitialisez la caméra ou zoomez avant de sélectionner.

## Lire les couleurs et annotations

1. Choisissez le mode dans la liste de couleurs : **LMGC90**, **Par type**, **Par matériau** ou **Par origine**.
2. Activez **DOF** pour afficher les indices visuels des opérations cinématiques configurées dans l’onglet DOF.
3. Activez **Lois** pour visualiser les liens issus des tables de visibilité (couleur candidate vers couleur antagoniste).
4. Ouvrez le filtre de groupe et choisissez un groupe pour isoler ses avatars. **Tous les groupes** réaffiche toute la scène.

Les couleurs par matériau et par origine servent à l’inspection visuelle ; elles ne changent ni les couleurs enregistrées dans les avatars ni les règles de visibilité.

## Exporter une image

1. Cadrez la scène avec la caméra et choisissez les filtres, couleurs et annotations à inclure.
2. Cliquez sur **📷 Exporter en PNG**.
3. Choisissez l’emplacement et le nom de l’image dans la boîte de dialogue.

## Lancer la visualisation native pylmgc90

1. Dans l’onglet **Visualisation 3D**, cliquez sur **pre.visuAvatars**.
2. Si pylmgc90 est disponible, l’application matérialise la scène puis ouvre le visualiseur natif.
3. Si le bouton indique que `pylmgc90` est indisponible, vérifiez que l’environnement Python utilisé pour lancer LMGC90_GUI contient bien cette bibliothèque.

Ce mode utilise les objets pylmgc90 réels et est distinct du rendu paramétrique PyVista. Il est indisponible sans pylmgc90 et peut désactiver la sélection individuelle du viewer intégré pendant son utilisation.

## Problèmes courants

| Symptôme | Vérification |
|---|---|
| La scène ne reflète pas la dernière modification | Cliquer sur **Rafraîchir la scène**. |
| Le viewer affiche « pyvista + pyvistaqt absents » | Installer ces dépendances dans l’environnement de l’application puis relancer celle-ci. |
| `pre.visuAvatars` indique pylmgc90 indisponible | Vérifier l’interpréteur/env utilisé par `lmgc90-gui`, et pas seulement un autre terminal. |
| Aucun avatar n’apparaît après actualisation | Vérifier que le projet contient des avatars/populations, puis réinitialiser la caméra. |
