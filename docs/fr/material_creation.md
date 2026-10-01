# Créer un matériau

L’onglet **Materials** contient la liste des matériaux du projet et un formulaire de création/modification. Les propriétés affichées changent en fonction du type sélectionné ; il ne s’agit pas d’un champ texte libre.

## Ajouter un matériau

1. Ouvrez **Onglets → Ouvrir → Materials** (`Ctrl+1`).
2. Saisissez un **Name** de cinq caractères maximum. Un nom peut être suggéré automatiquement selon le type.
3. Choisissez **Type**.
4. Renseignez **Density** si le champ est activé. La densité est utilisée par LMGC90 pour les types qui la prennent en charge.
5. Complétez les champs dans **Propriétés (selon type / anisotropie)**. Les choix et les champs numériques sont adaptés au matériau choisi.
6. Cliquez sur **Add**. Une erreur de validation apparaît si un nom ou une propriété requise est invalide.
7. Sélectionnez une ligne du tableau pour recharger ses valeurs. Modifiez-les puis cliquez sur **Update**.
8. Pour supprimer un matériau, sélectionnez-le et cliquez sur **Delete**. Si d’autres objets le référencent, corrigez d’abord ces dépendances.
9. Cliquez sur **Clear form** pour préparer une nouvelle entrée.

Les valeurs initiales servent de point de départ, pas de caractérisation automatique du matériau réel. Vérifiez unités et constantes physiques avant le calcul.

## Paramètres proposés par type

Les champs exacts reflètent les options acceptées par pylmgc90 dans l’environnement courant.

| Type | Champs principaux de l’interface | Notes |
|---|---|---|
| `RIGID` | Aucun champ spécifique | Utiliser **Density**. |
| `ELAS` | `elas`, `anisotropy`, `young`, `nu`, `G` ou constantes directionnelles | Seul type où l’interface propose `orthotropic`. |
| `ELAS_DILA` | `elas`, isotropie, `young`, `nu`, `dilatation`, `T_ref_meca` | Pas de `G` ni de champs orthotropes. |
| `VISCO_ELAS` | `elas`, isotropie, `young`, `nu`, `viscous_model`, `viscous_young`, `viscous_nu` | Pas de champ `viscosity` ni de `G`. |
| `ELAS_PLAS` | `young`, `nu`, `critere`, `isoh`, `iso_hard`, `isoh_coeff`, `cinh`, `visc` | Les choix sont fournis par des listes contrôlées. |
| `THERMO_ELAS` | `young`, `nu`, `dilatation`, `T_ref_meca`, `conductivity`, `specific_capacity` | `conductivity` et `specific_capacity` acceptent une valeur ou `field`. |
| `PORO_ELAS` | `young`, `nu`, `hydro_cpl`, `conductivity`, `specific_capacity` | `conductivity` et `specific_capacity` acceptent une valeur ou `field`. |
| `DISCRETE` | `masses`, `stiffnesses`, `viscosities` | Saisir un vecteur 2D ou 3D ; le champ densité est désactivé. |
| `USER_MAT` | `file_mat` | Indiquer le chemin/nom de la loi matériau selon la configuration LMGC90. |
| `EXTERNAL` | Aucun champ de propriété | Le champ densité est désactivé ; le comportement est géré à l’extérieur. |

### Élastique isotrope et orthotrope

Pour `ELAS`, choisissez `isotropic` pour renseigner **Young** et **Poisson** ; `G` est également proposé. Pour une loi orthotrope, choisissez `orthotropic` : les propriétés isotropes sont remplacées par celles des axes matériels.

- En 2D : `young1`, `young2`, `nu12`, `G12`.
- En 3D : `young1`, `young2`, `young3`, `nu12`, `nu13`, `nu23`, `G12`, `G13`, `G23`.

Les champs exclusivement 3D sont masqués dans un projet 2D. Les types `ELAS_DILA`, `VISCO_ELAS`, `ELAS_PLAS`, `THERMO_ELAS` et `PORO_ELAS` restent isotropes dans ce formulaire : ne tentez pas de leur ajouter des propriétés orthotropes.

### Options visqueuses

Pour `VISCO_ELAS`, utilisez `viscous_model` (`none` ou `KelvinVoigt`) puis les propriétés `viscous_young` et `viscous_nu` si le modèle visqueux est actif. Les anciennes propriétés nommées `eta` ou `viscosity` ne sont pas des options acceptées par cette version de pylmgc90 et ne doivent pas être saisies.

### Élasto-plasticité

`ELAS_PLAS` propose notamment le critère `Von-Mises` ou `none`, les modèles d’écrouissage isotrope/cinématique et leur paramétrage. Choisissez des valeurs cohérentes entre `isoh`, `cinh` et `visc` ; pylmgc90 valide les choix au moment de la matérialisation.

## Paramètres numériques particuliers

- Les valeurs numériques sont saisies dans les champs prévus. Les contrôles de l’interface exposent les propriétés selon le type choisi.
- Pour `THERMO_ELAS` et `PORO_ELAS`, saisissez `field` dans les champs de conductivité/capacité lorsqu’elles sont portées par le modèle éléments finis plutôt que par un scalaire.
- Pour `DISCRETE`, saisissez les composantes séparées par des virgules, par exemple `1, 1` en 2D ou `1, 1, 1` en 3D. Chaque vecteur doit avoir la même dimension que le projet.
- `RIGID` n’a pas de propriété complémentaire ; renseignez la densité.

## Exemple : matériau élastique acier

1. Ouvrez **Materials**.
2. Choisissez `ELAS`.
3. Saisissez un nom tel que `STEEL` (5 caractères maximum).
4. Gardez `isotropic`.
5. Renseignez **Density** à environ `7850` kg/m³, **Young** à `2.1e11` Pa et **Poisson** à `0.3`.
6. Cliquez sur **Add**.
7. Créez ensuite un modèle mécanique et associez ce matériau à un avatar.

## Mise à jour et suppression

Sélectionnez le matériau dans la liste avant de cliquer sur **Update**. Vérifiez le nom : si vous saisissez un nom déjà utilisé, ajoutez un nouveau matériau avec **Add** ou mettez à jour explicitement l’entrée sélectionnée.

La suppression n’est pas un moyen de renommer ou de remplacer automatiquement toutes les références. Réassignez d’abord les avatars concernés à un autre matériau si l’application signale une dépendance.

## Variables dynamiques

Les champs numériques prenant en charge les expressions peuvent utiliser les variables du projet. Ouvrez **Tools → Variables dynamiques…** (`Ctrl+V`) pour les créer, voir leur valeur résolue et les modifier. Le dialogue et les limites d’expression sont détaillés dans [Variables dynamiques](dynam_variables.md).
