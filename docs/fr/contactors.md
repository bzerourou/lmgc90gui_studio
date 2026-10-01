# Contacteurs

Les contacteurs définissent les formes par lesquelles un avatar participe aux détections de contact. Ils sont distincts de la géométrie principale, de la loi de contact et de la table de visibilité : pour un contact exploitable, vérifiez ces trois éléments.

## Ajouter un contacteur

1. Créez d’abord l’avatar dans **Avatars**. Un avatar vide ou maillé est un cas courant, mais les corps rigides peuvent aussi recevoir des contacteurs compatibles supplémentaires.
2. Ouvrez **Onglets → Ouvrir → Contactors**.
3. Dans **Select avatar**, choisissez le corps à modifier.
4. Dans **Shape**, choisissez l’une des formes proposées. La liste dépend du type d’avatar et de la dimension du projet ; n’utilisez pas un contacteur d’une autre dimension.
5. Saisissez **Color**. Le code de couleur identifie le contacteur dans les tables de visibilité ; utilisez le même code dans les deux endroits.
6. Pour un corps maillé, renseignez éventuellement **by group** afin de limiter le contacteur à un groupe de nœuds ou de faces.
7. Cliquez sur **Add contactor**. La nouvelle forme apparaît dans **Contactors on avatar**.
8. Répétez les étapes pour ajouter plusieurs contacteurs si le modèle en a besoin.

## Retirer un contacteur

1. Sélectionnez sa ligne dans **Contactors on avatar**.
2. Cliquez sur **Remove selected**.

Cette action enlève la définition du contacteur de l’avatar sélectionné ; elle ne supprime pas l’avatar.

## Familles de formes usuelles

| Corps / dimension | Contacteurs souvent proposés |
|---|---|
| Rigide 2D | `DISKx`, `xKSID`, `JONCx`, `POLYG`, `PT2Dx` |
| Rigide 3D | `SPHER`, `PLANx`, `CYLND`, `POLYR`, `PT3Dx` |
| Maillé 2D | `CLxxx`, `ALpxx`, `PT2Dx` |
| Maillé 3D | `CSpxx`, `ASpxx`, `PT3Dx` |

La liste effective est calculée par l’application selon l’avatar. Elle peut être plus courte que ce tableau. Les formes dépendent aussi du rôle prévu : les contacteurs de grain sont souvent candidats, tandis qu’une paroi sert souvent d’antagoniste.

## Relier le contacteur aux interactions

Après la création du contacteur :

1. Vérifiez sa couleur et sa forme dans **Contactors**.
2. Ouvrez **Contact** et créez la loi appropriée si elle n’existe pas encore.
3. Ouvrez **Visibility**. Sélectionnez le corps, le contacteur et la couleur correspondants dans les champs candidat/antagoniste.
4. Choisissez la loi créée et définissez la distance **Alert**.
5. Cliquez sur **Add**, puis sur **Vérifier** pour repérer les couleurs ou lois non associées.

Les couleurs et formes réellement présentes sont suggérées dans **Visibility**. Si la combinaison choisie n’existe pas sur un avatar du projet, l’application demande une confirmation avant d’enregistrer la table.
