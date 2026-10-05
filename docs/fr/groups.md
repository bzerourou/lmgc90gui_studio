# Groupes d’avatars

L’onglet **Groups** permet de réunir plusieurs avatars sous un même nom. Un groupe peut servir de cible pour les opérations DOF, les extractions de post-traitement et le filtre de la visualisation 3D.

![](../captures/groups.png)

## Créer un groupe

1. Ouvrez **Onglets → Ouvrir → Groups**.
2. Dans **Members**, sélectionnez les avatars à inclure. La sélection multiple est activée ; cliquez sur un avatar sélectionné pour le désélectionner.
3. Saisissez un nom dans le champ **group name**. L’application propose un nom unique si le champ est vide.
4. Cliquez sur **New / Update**.
5. Le groupe apparaît dans **Existing groups** avec le nombre de membres.

La liste des membres identifie les avatars par un identifiant abrégé, leur type et leur centre. Elle ne dépend pas de la position de l’avatar dans la liste.

## Modifier un groupe

1. Sélectionnez le groupe dans **Existing groups**.
2. Vérifiez les avatars sélectionnés dans **Members**.
3. Ajoutez ou retirez des membres par sélection.
4. Cliquez sur **New / Update** pour enregistrer la nouvelle composition sous ce nom.

Un nom existant sert donc à mettre à jour le groupe correspondant. Vérifiez le nom avant de valider pour éviter de remplacer la composition d’un groupe voulu.

## Supprimer un groupe

1. Sélectionnez le groupe dans **Existing groups**.
2. Cliquez sur **Delete group**.

La suppression retire le groupe, pas les avatars qui le composent. Les opérations ou commandes qui visaient ce nom ne sont pas automatiquement redirigées vers un autre groupe.

## Groupes créés par d’autres outils

Les assistants de maçonnerie et certaines générations paramétriques ou granulométriques peuvent enregistrer un groupe automatiquement. Il apparaît dans **Existing groups** et peut ensuite être ciblé dans les onglets appropriés.

Les groupes manuels contiennent des avatars individuels. Les populations massives SoA ne sont pas une sélection de lignes d’avatars dans ce panneau ; elles sont identifiées et gérées depuis **Granulo**.

## Utiliser un groupe

- **DOF** : choisir `group` dans **Target type**, puis sélectionner le nom du groupe dans **Target value**.
- **Post-pro** : choisir `group` dans **Target type**, puis indiquer le groupe ciblé.
- **Visualisation 3D** : sélectionner le nom dans le filtre de groupe pour n’afficher que ses avatars.

Si un groupe n’est pas proposé dans un onglet, vérifiez d’abord qu’il contient des avatars et que la liste a été rafraîchie après sa création.
