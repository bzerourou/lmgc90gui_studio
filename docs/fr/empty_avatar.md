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
Sans contacteur, il n’a pas de géométrie de contact à dessiner. `visuAvatars`
l’ignore alors ; le journal indique combien d’avatars ont été ignorés. Ajoutez au
moins un contacteur pour voir sa forme dans le visualiseur natif.

## Ajouter ses contacteurs

1. Ouvrez **Onglets → Ouvrir → Contactors**.
2. Sélectionnez l’avatar vide dans **Select avatar**.
3. Choisissez une forme proposée dans **Shape**. La liste est filtrée selon le type de corps et la dimension.
4. Renseignez les paramètres géométriques affichés pour cette forme (par exemple **byrd** pour le rayon de `DISKx`, ou **axe1/axe2** pour `JONCx`). Le champ **shift** décale le contacteur depuis le centre de l’avatar ; il prend deux coordonnées en 2D et trois en 3D.
   Pour `POLYG` et `POLYR`, choisissez **generation_type** : **regular** demande le nombre de sommets et le rayon ; **full** demande les sommets, ainsi que la connectivité triangulaire des faces pour `POLYR`. Les sommets d’un `POLYG` complet doivent être donnés dans le sens anti-horaire.
5. Renseignez **Color**. Utilisez un code de 5 caractères cohérent avec les tables de visibilité à créer.
6. Pour un corps maillé, indiquez éventuellement **Group** pour limiter le contacteur à un groupe d’éléments.
7. Cliquez sur **Add contactor** et vérifiez la ligne ajoutée.
8. Pour retirer une forme, sélectionnez-la et cliquez sur **Remove selected**.

Après ajout ou suppression, cliquez sur **Rafraîchir la scène** dans le viewer 3D.
Le bouton **pre.visuAvatars** reconstruit également les corps pylmgc90 depuis le projet ;
un contacteur sans ses dimensions requises n’est pas créé.

# Avatar mesh

Il est tout à fait possible de créer un avatar déformbale afin d'intéragir rigid/déformable. Pour cela il faut opter sur l'élément **mesh**.

### Corps déformable 2D — `mesh_shapes_2d`

Ces formes sont destinées à être ajoutées sur un maillage FEM 2D. Elles définissent des contacteurs de surface pour les interactions rigide-déformable.

| Forme | Description | Usage |
|-------|-------------|-------|
| `ALpxx` | Contacteur ligne pour maçonnerie FEM 2D | Interactions `ALpMECAx` (CLALp / MECAx) |
| `CLxx` | Contacteur ligne continu 2D | Interactions `DKMECAx` (disque / MECAx) |
| `DISKL` | Disque sur nœud FEM 2D | Interaction disque-disque sur maillage |
| `PT2TL` | Point de transmission 2D | Couplage nœud-nœud FEM |

### Corps déformable 3D — `mesh_shapes_3d`

| Forme | Description | Usage |
|-------|-------------|-------|
| `ASpxx` | Contacteur surface pour sphères FEM 3D | Interactions `SPMECAx` (sphère / MECAx 3D) |
| `CSpxx` | Contacteur surface continu 3D | Interactions rigide-déformable 3D génériques |
| `PT3Dx` | Nœud ponctuel FEM 3D | Couplage nœud-nœud FEM 3D |

---

>**Remarque** : Un même avatar peut porter plusieurs contacteurs de couleurs ou formes distinctes. Chaque couple forme/couleur utilisé dans une interaction doit être correctement repris dans **Visibility**.

## Configurer le contact

1. Créez une loi dans **Contact**.
2. Dans **Visibility**, choisissez le corps, la forme et la couleur du contacteur comme candidat ou antagoniste.
3. Associez la loi et une distance **Alert** adaptée à l’échelle de la scène.
4. Cliquez sur **Add**, puis sur **Vérifier** pour rechercher les couleurs sans table ou les lois non référencées.


---

Voir [Contacteurs](contactors.md), [Lois de contact](contact_laws.md) et [Tables de visibilité](visibility.md) pour les formulaires correspondants.
