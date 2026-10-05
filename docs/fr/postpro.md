# Configurer le post-traitement

L’onglet **Post-pro** ajoute des commandes d’extraction au calcul. Il configure ce que le calcul doit écrire ; il ne sert pas à ouvrir ou analyser les fichiers de résultats après exécution.

![](../captures/postpro.png)

## Ajouter une commande

1. Ouvrez **Onglets → Ouvrir → Post-pro**.
2. Choisissez une valeur de **Command** ou saisissez le nom d’une commande acceptée par votre installation LMGC90.
3. Réglez **Step**, la fréquence d’écriture.
4. Choisissez **Target type** : `global`, `avatar` ou `group`.
5. Pour une cible `avatar`, sélectionnez l’avatar ; pour `group`, choisissez le groupe. Pour `global`, aucune cible n’est nécessaire.
6. Cliquez sur **Add**.
7. Vérifiez la commande dans la liste : nom, fréquence et cible.

Les noms préremplis comprennent notamment `SOLVER INFORMATIONS`, `BODY TRACKING`, `TORQUE EVOLUTION`, `KINETIC ENERGY`, `COORDINATE` et `VAN_DER_WAALS`. Les commandes doivent être compatibles avec les données et le calcul configurés.

## Retirer une commande

1. Sélectionnez la commande dans la liste.
2. Cliquez sur **Remove**.

L’onglet ne propose pas d’édition en place : retirez une commande mal définie puis recréez-la avec les bons paramètres.

## Extractions avancées des routines chipy

Pour régler les sorties avancées, ouvrez **Compute**, puis **Configurer les routines chipy…**. Le dialogue comprend notamment les onglets **Extraction**, **Inspect. 2D**, **Inspect. 3D** et **Inspect. Interact.**. Ils configurent les vecteurs d’état, forces, énergie, champs FEM, visibilité et inspecteurs selon le type de corps.

## Consulter les journaux

- Le journal de l’onglet **Compute** affiche la sortie du processus de calcul.
- **Computation → Application journal** (`F7`) affiche les erreurs et événements internes de LMGC90_GUI.

Ces journaux ne sont pas un visualiseur des résultats calculés. Pour inspecter la scène de prétraitement, utilisez [Visualisation](visualisation.md).
