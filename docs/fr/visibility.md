# Tables de visibilité

Une table de visibilité (see-table) déclare une paire de contacteurs susceptible d’interagir, les couleurs à considérer, la loi de contact à utiliser et la distance d’alerte. Elle ne crée ni avatar, ni contacteur, ni loi.

## Créer une table

1. Créez d’abord les avatars et populations qui doivent interagir.
2. Assurez-vous que leurs matériaux et modèles sont définis et, si nécessaire, que leurs contacteurs sont dans **Contactors**.
3. Créez une loi dans **Contact**.
4. Ouvrez **Onglets → Ouvrir → Visibility** (`Ctrl+8`).
5. Dans **Corps candidat**, choisissez le type de corps mobile. Les choix suivent la dimension du projet et les types de corps présents.
6. Choisissez **Shape candidat (mobile)**. La liste privilégie les contacteurs réels des corps compatibles avec le rôle candidat.
7. Choisissez **Color candidat**. Pour la forme sélectionnée, l’application propose les couleurs effectivement associées à ces contacteurs.
8. Choisissez **Corps antagoniste**, **Shape antagoniste (obstacle)** et **Color antagoniste** de la même manière.
9. Sélectionnez **Law (behav)** parmi les lois du projet.
10. Réglez **Alert**, distance de détection avant contact, en unités cohérentes avec la géométrie.
11. Cliquez sur **Add**.

La liste du formulaire est chaînée : changer le corps actualise les formes, et changer la forme actualise les couleurs. Les listes de formes et de couleurs restent éditables pour permettre les cas spécialisés. Si une combinaison libre ne correspond à aucun contacteur du projet, l’application demande confirmation avant l’enregistrement. Chaque code couleur doit contenir exactement cinq caractères.

## Règles usuelles

### Grains entre eux

1. Vérifiez la couleur et le contacteur des grains (souvent `DISKx` en 2D ou `SPHER` en 3D).
2. Cliquez sur **Grains↔grains** pour préremplir une paire homogène.
3. Vérifiez la couleur, la loi et la distance d’alerte avant de cliquer sur **Add**.

### Grains contre un mur ou le sol

1. Cliquez sur **Grains↔sol** pour proposer un contacteur mobile et un contacteur antagoniste usuels.
2. Sélectionnez la couleur du grain et celle de la paroi à partir des couleurs de la scène.
3. Vérifiez le corps, la loi et **Alert**, puis ajoutez la table.

Les presets remplissent des champs ; ils ne remplacent pas la vérification des formes et couleurs réellement utilisées dans le projet.

## Modifier, supprimer et rafraîchir

- Pour modifier une table, sélectionnez sa ligne, corrigez le formulaire puis cliquez sur **Update**.
- Pour la supprimer, sélectionnez-la puis cliquez sur **Delete**.
- **Listes** recharge les propositions après modification des avatars, des contacteurs ou de leurs couleurs.
- **Clear form** désélectionne la ligne en cours.
- **Lier A ↔ B** ouvre un dialogue compact pour relier deux couleurs/groupes. Il utilise les mêmes propositions de formes et de couleurs.

Une table ne crée pas automatiquement la loi ; si **Law (behav)** pointe vers un nom inconnu, la vérification le signale.

## Contrôler la configuration

1. Cliquez sur **Vérifier**.
2. Lisez les avertissements : couleur d’avatar sans table, loi jamais référencée, nom de loi inconnu ou absence de table alors que la scène contient des corps.
3. Corrigez chaque association dans **Visibility**, **Contact** ou **Contactors** selon le cas.
4. Relancez la vérification.

Ce contrôle est un diagnostic de cohérence des couleurs et des noms de lois. Il ne prouve pas que tous les détecteurs ou paramètres du solveur sont adaptés ; contrôlez également **Compute** avant le calcul.

## Comprendre les types de corps

- `RBDY2` : corps rigides 2D.
- `RBDY3` : corps rigides 3D.
- `MAILx` : corps déformables maillés.
- `MBS2D` et `MBS3D` : familles de corps multicorps proposées lorsque pertinentes.

Les formes proposées dépendent de la dimension, du type d’avatar et des contacteurs réellement configurés. Pour un avatar maillé, par exemple, les contacteurs de bord doivent être définis dans **Contactors** ou dans l’assistant de maillage avant de bâtir la table.
