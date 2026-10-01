# Granulométrie et populations de particules

L’onglet **Granulo** génère une population de particules dont les rayons sont compris entre deux bornes, et les place dans un conteneur. Une population SoA permet de représenter de nombreux grains sans créer une ligne graphique individuelle pour chaque particule.

## Préparer le projet

1. Créez un matériau compatible avec les grains dans **Materials**.
2. Créez un modèle rigide adapté à la dimension (`MECAx` avec `Rxx2D` ou `Rxx3D`) dans **Models**.
3. Ouvrez **Onglets → Ouvrir → Granulo** (`Ctrl+6`).

## Régler le dépôt

1. Indiquez **N particules**.
2. Renseignez **Rayon min** et **Rayon max**. Le rayon minimum doit être strictement inférieur au maximum.
3. Choisissez le **Conteneur** proposé pour la dimension du projet :
   - 2D : `Box2D`, `Disk2D`, `Drum2D`, `Couette2D` ;
   - 3D : `Box3D`, `Sphere3D`, `Cylinder3D`.
4. Complétez les dimensions du conteneur affichées sous **Conteneur** : `lx`, `ly`, `lz`, `r`, `rint` ou `rext` selon le cas.
5. Choisissez le **Type d’avatar**. En 2D : disque, disque discret ou polygone ; en 3D : sphère ou polyèdre.
6. Sélectionnez **Matériau** et **Modèle**.
7. Renseignez **Couleur (5 car.)** et **Groupe (5 car.)**.
8. Réglez **Seed** pour reproduire le tirage. La valeur `random` demande une graine aléatoire.

## Choisir un mode de génération

- **Dépôt NumPy SoA** : laissez **Utiliser dépôt pylmgc (engine) si disponible** décoché. L’application construit une population compacte et l’ajoute au projet.
- **Dépôt pylmgc** : cochez cette option si pylmgc90 est disponible dans l’environnement et que vous souhaitez utiliser ses routines de dépôt.
- **Distribution seule** : cochez **Distribution seule (rayons)** pour générer et enregistrer les rayons sans produire d’avatars ni de population. Dans ce mode, le dépôt pylmgc est désactivé.

## Générer et contrôler le résultat

1. Relisez le nombre, les rayons, le conteneur, le type de corps et les références matériau/modèle.
2. Cliquez sur **Générer le dépôt**.
3. Vérifiez le message de confirmation.
4. La liste présente les populations créées sous la forme `[SoA]` avec leur effectif, leur type et leur groupe. Les distributions seules sont repérées par `[dist]`.
5. Pour retirer une population, sélectionnez-la dans la liste puis cliquez sur **Supprimer sélection**.
6. Ouvrez **Visualisation 3D** et cliquez sur **Rafraîchir la scène** pour voir la population.

La suppression proposée concerne une population ; vérifiez la ligne sélectionnée avant de valider.

## Dimension et contact

Le type de conteneur doit correspondre à la dimension du projet. Les populations génèrent leurs propres corps rigides/couleurs, mais les interactions nécessitent encore des lois et des tables de visibilité compatibles. Dans **Visibility**, utilisez les couleurs et contacteurs proposés depuis la population ; choisissez la bonne paire candidat/antagoniste et une distance **Alert** cohérente.

Pour répéter une génération avec une variable d’itération, consultez [ForLoop](for_loop.md). Pour comprendre la représentation des grandes populations, voir [Populations de particules](particle_population.md) (référence technique).
