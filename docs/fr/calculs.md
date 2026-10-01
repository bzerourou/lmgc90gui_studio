# Préparer et lancer un calcul

L’onglet **Compute** configure le script de calcul `command.py`, prépare le répertoire de travail et peut lancer le processus chipy. La disponibilité de pylmgc90 dans l’environnement qui exécute LMGC90_GUI détermine les fonctions natives accessibles.

## Ouvrir l’onglet Compute

- Choisissez **Onglets → Ouvrir → Compute** lorsque cette entrée est disponible dans votre construction de l’application.
- Le raccourci `F5` depuis la fenêtre principale ouvre également l’onglet et déclenche l’action de calcul.

L’onglet affiche un résumé de la dimension, du nombre d’avatars et de particules, des lois, tables de visibilité, DOF et corps déformables détectés. Vérifiez qu’il correspond au projet préparé.

## Régler les paramètres de base

1. Dans **Paramètres temporels**, définissez **Pas de temps (dt)**, **Nombre d’itérations** et **Theta intégrateur**.
2. Dans **Solveur de contact**, réglez **Tolérance**, **Relaxation**, **Norme**, **Itérations GS1**, **Itérations GS2** et **Type de solveur**.
3. Dans **Sorties**, indiquez les fréquences **WriteOut** et **Display**.
4. Activez ou désactivez **Disable chipy log messages** selon que vous souhaitez réduire la sortie standard.
5. Activez **ReadDatbox(deformable=True)** si la scène comporte des corps déformables. Le résumé peut également détecter un maillage.

Les valeurs initiales de l’interface sont des paramètres de départ, pas une garantie de stabilité ou de convergence. Adaptez le pas de temps, le solveur et les fréquences à l’échelle du problème.

## Configurer les routines chipy

1. Cliquez sur **Configurer les routines chipy…**.
2. Dans **Modele**, vérifiez l’hypothèse, la physique et les paramètres de modèle proposés.
3. Dans **Routines**, activez les familles de corps et détecteurs nécessaires aux paires de contact du projet. Pour des corps déformables, activez également les routines FEM et les contacteurs mixtes pertinents.
4. Dans **Extraction**, choisissez visualisation, visibilité des avatars, vecteurs d’état, forces et énergies requis.
5. Dans **Pilotage**, configurez au besoin le redémarrage, le critère d’arrêt et les pas de temps multiples.
6. Réglez les onglets **Inspect. 2D**, **Inspect. 3D** et **Inspect. Interact.** si des fonctions d’inspection sont nécessaires.
7. Utilisez **Apercu du script command.py** pour examiner le script généré.
8. Validez avec **OK** ou abandonnez avec **Cancel**. **Restore Defaults** rétablit les valeurs par défaut du dialogue.

Les détecteurs cochés doivent couvrir les types de contacteurs effectivement présents et les tables de visibilité du projet. Une table ne suffit pas si le détecteur correspondant n’est pas activé.

## Choisir le répertoire et préparer les fichiers

1. Dans **Répertoire de calcul**, saisissez le chemin de travail ou cliquez sur **Parcourir…**.
2. Cliquez sur **💾 Sauver → préférences** si vous souhaitez réutiliser ces réglages ultérieurement.
3. Cliquez sur **📦 Préparer DATBOX / scripts**.
4. L’application écrit `pre.py` et `command.py` dans le répertoire sélectionné.
5. La création de `DATBOX` dépend des préférences d’écriture automatique et de la disponibilité de pylmgc90.
6. Vérifiez le message de confirmation ainsi que le journal de préparation.

Le menu **Computation → Generate DATBOX / scripts…** (`Ctrl+F5`) offre également une action de préparation/export. Pour exporter uniquement les scripts ou l’ensemble depuis des boîtes de dialogue de sauvegarde, utilisez **Tools → Generate pre.py…**, **Generate command.py…** ou **Export all…**.

## Lancer et arrêter le calcul

1. Vérifiez le chemin du répertoire de travail.
2. Cliquez sur **▶ Lancer le calcul (F5)** ou utilisez `F5`.
3. Si `command.py` est absent, acceptez sa préparation si vous souhaitez poursuivre.
4. Confirmez le répertoire et la commande si la confirmation de lancement est activée dans les préférences.
5. Suivez les lignes du journal dans l’onglet Compute.
6. Cliquez sur **⏹ Stop** pour demander l’arrêt du processus.
7. À la fin, vérifiez le statut et le code de retour (`rc`).

Le processus tourne séparément afin de laisser l’interface réactive. Un lancement exige un interpréteur Python et des dépendances LMGC90 fonctionnels dans l’environnement sélectionné.

## Préférences et diagnostic

- **📥 Charger préférences** recharge les paramètres enregistrés.
- **💾 Sauver → préférences** mémorise les paramètres de calcul et le répertoire de travail.
- Le journal de calcul contient les sorties du processus.
- **Computation → Application journal** (`F7`) fournit le journal interne de l’application.

La page [Post-traitement](postpro.md) décrit les commandes d’extraction ; la page [Visualisation](visualisation.md) décrit l’inspection de la scène avant calcul. L’application actuelle ne fournit pas un écran complet de parcours des fichiers de résultats calculés.
