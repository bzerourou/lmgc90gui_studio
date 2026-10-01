# Avatar vide

`emptyAvatar` crée un corps sans forme de contact définie par défaut. Ajoutez ensuite un ou plusieurs contacteurs dans l’onglet **Contactors**. L’ancien onglet indépendant « Empty Avatar » n’existe plus.

## Créer le corps vide

1. Créez le matériau et le modèle compatibles avec la dimension du projet.
2. Ouvrez **Avatars** (`Ctrl+3`).
3. Choisissez `emptyAvatar` dans **Type**.
4. Indiquez son centre X/Y et, en 3D, Z.
5. Choisissez **Material** et **Model**, puis indiquez **Color**.
6. Cliquez sur **Add**.

Un avatar vide ne possède pas de champ géométrique supplémentaire dans **Type parameters**.

## Ajouter ses contacteurs

1. Ouvrez **Onglets → Ouvrir → Contactors**.
2. Sélectionnez l’avatar vide dans **Select avatar**.
3. Choisissez une forme proposée dans **Shape**. La liste est filtrée selon le type de corps et la dimension.
4. Renseignez **Color**. Utilisez un code de 5 caractères cohérent avec les tables de visibilité à créer.
5. Ajoutez éventuellement un groupe dans **by group** si la forme est associée à une sélection de nœuds ou faces.
6. Cliquez sur **Add contactor** et vérifiez la ligne ajoutée.
7. Pour retirer une forme, sélectionnez-la et cliquez sur **Remove selected**.

Un même avatar peut porter plusieurs contacteurs de couleurs ou formes distinctes. Chaque couple forme/couleur utilisé dans une interaction doit être correctement repris dans **Visibility**.

## Configurer le contact

1. Créez une loi dans **Contact**.
2. Dans **Visibility**, choisissez le corps, la forme et la couleur du contacteur comme candidat ou antagoniste.
3. Associez la loi et une distance **Alert** adaptée à l’échelle de la scène.
4. Cliquez sur **Add**, puis sur **Vérifier** pour rechercher les couleurs sans table ou les lois non référencées.

Voir [Contacteurs](contactors.md), [Lois de contact](contact_laws.md) et [Tables de visibilité](visibility.md) pour les formulaires correspondants.
