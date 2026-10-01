# Créer un modèle

L’onglet **Models** associe une famille physique et un élément fini à une dimension. Dans l’application actuelle, le formulaire standard ne contient pas la longue section d’options numériques décrite dans les anciennes captures.

## Créer un modèle

1. Ouvrez **Onglets → Ouvrir → Models** (`Ctrl+2`).
2. Saisissez un **Name** de cinq caractères maximum. Une proposition de nom peut apparaître automatiquement.
3. Choisissez **Physics** : `MECAx`, `THERx`, `POROx` ou `MULTI`.
4. Choisissez **Element** dans la liste. Elle est actualisée selon la physique et la dimension du projet.
5. Vérifiez **Dimension (project)**. Cette dimension est héritée du projet ; elle ne se règle pas dans le formulaire du modèle.
6. Cliquez sur **Add**.
7. Vérifiez que le modèle apparaît dans le tableau.

Un nom déjà utilisé ne crée pas une deuxième entrée : sélectionnez le modèle existant et choisissez **Update** pour le modifier.

## Modifier ou supprimer

1. Cliquez sur la ligne du modèle dans la liste.
2. Les champs **Name**, **Physics** et **Element** sont rechargés.
3. Modifiez les valeurs puis cliquez sur **Update**.
4. Pour supprimer le modèle sélectionné, cliquez sur **Delete**. Vérifiez auparavant qu’aucun avatar ou configuration ne le référence.
5. Utilisez **Clear form** pour abandonner la sélection et préparer une nouvelle entrée.

## Choisir la physique et l’élément

- `MECAx` : modèles mécaniques. En 2D, `Rxx2D` est l’élément usuel des corps rigides ; en 3D, `Rxx3D`. La liste contient aussi les éléments finis disponibles dans le catalogue de l’application.
- `THERx` : éléments thermiques disponibles pour la dimension sélectionnée.
- `POROx` : éléments poromécaniques mixtes, disponibles seulement pour les combinaisons prévues dans le catalogue.
- `MULTI` : éléments mécaniques/multiphysiques proposés pour la dimension.

La liste déroulante est la référence pour les choix disponibles avec la version installée ; elle se met à jour lorsque vous changez la physique.

## Modèle rigide : exemples

### Corps rigide 2D

1. Assurez-vous que le projet est en 2D.
2. Dans **Models**, saisissez par exemple `rigid`.
3. Choisissez `MECAx`.
4. Choisissez `Rxx2D`.
5. Cliquez sur **Add**.

### Corps rigide 3D

1. Créez ou utilisez un projet 3D.
2. Saisissez un nom court, par exemple `rig3D`.
3. Choisissez `MECAx`, puis `Rxx3D`.
4. Cliquez sur **Add**.

## Modèle d’éléments finis

1. Créez un projet de la dimension souhaitée.
2. Dans **Models**, choisissez une physique compatible avec l’analyse envisagée.
3. Sélectionnez l’élément proposé correspondant au type de maillage qui sera construit ou importé.
4. Cliquez sur **Add**.
5. Associez ce modèle à un matériau adapté dans **Materials**, puis choisissez-le lors de la création du corps dans **Avatars** ou dans l’assistant **Deformable**.

L’assistant de corps déformable possède des options supplémentaires propres à son parcours de maillage. Elles ne sont pas des champs de l’onglet **Models** : voir [Assistant de corps déformable](meshed.md).

## Cohérence avec les avatars

- Les avatars rigides 2D attendent généralement un modèle de dimension 2 avec élément `Rxx2D`.
- Les avatars rigides 3D attendent généralement un modèle de dimension 3 avec élément `Rxx3D`.
- Les avatars maillés nécessitent un élément fini compatible avec la dimension.
- La dimension du projet, du modèle et du corps doit correspondre.

Si vous devez changer la dimension du projet, passez par **Project → Set dimension…** et examinez l’avertissement avant de confirmer. Le changement ne convertit pas automatiquement les modèles ou avatars existants.
