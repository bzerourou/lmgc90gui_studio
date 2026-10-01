# Assistant de corps déformable

L’assistant **Mesh déformable** guide la création d’un corps maillé et de ses contacteurs de bord. Il est accessible depuis **Tools → Assistant Mesh déformable…** (`Ctrl+Shift+D`) ou l’onglet **Deformable**.

## Ouvrir l’assistant

1. Ouvrez **Deformable** depuis **Onglets → Ouvrir** et cliquez **Ouvrir l’assistant MeshWizard…**, ou choisissez la commande dans **Tools**.
2. Lisez l’introduction puis cliquez sur **Suivant**. **Retour** revient à la page précédente ; **Annuler** ferme l’assistant.

## Parcours des pages

1. **Dimension** : sélectionnez 2D ou 3D conformément au projet. Si des avatars ou modèles existent déjà, leur dimension doit rester cohérente.
2. **Matériau** : créez un matériau élastique parmi les types proposés, ou choisissez un matériau existant de même usage. Complétez les champs requis.
3. **Modèle EF** : créez un modèle ou réutilisez un modèle compatible en dimension. Si vous en créez un, choisissez physique, élément et options proposées (anisotropie, cinématique, formulation et stockage de masse).
4. **Géométrie** : choisissez une forme disponible :
   - en 2D : **Rectangle**, **Disque**, **Fichier externe** ;
   - en 3D : **Boîte (H8)**, **Sphère**, **Cylindre**, **Fichier externe**.
5. Renseignez le centre et les dimensions, rayon ou hauteur demandés par la géométrie.
6. Pour **Fichier externe**, cliquez **Parcourir…** puis choisissez un format affiché dans le sélecteur, tel que `.msh`, `.vtk`, `.brep`, `.step`, `.iges` ou `.geo`.
7. **Raffinement** : choisissez le type de maillage proposé puis réglez les subdivisions actives : `nx`, `ny`, `nz`, `nr`, `ntheta` ou `nphi`. Des valeurs plus élevées donnent davantage d’éléments et peuvent accroître le coût de calcul.
8. **Contacteurs de bord** : conservez **Ajouter un contacteur de bord** si le corps doit interagir. Choisissez sa forme compatible avec la dimension et sa couleur. **by group** est facultatif.
9. **Résumé** : vérifiez la dimension, le matériau, le modèle, la géométrie, le raffinement et les contacteurs.
10. Cliquez sur **Générer le maillage**. L’assistant confirme la création ou affiche l’erreur à corriger.

## Formes et maillage effectivement produits

Le rectangle 2D utilise la construction structurée disponible dans l’application. Pour les autres géométries et les fichiers externes, l’assistant enregistre l’intention de maillage et ses paramètres dans le projet ; la génération/matérialisation complète dépend de l’export et des outils LMGC90 présents dans l’environnement.

Le bouton **Parcourir…** enregistre un chemin : ce n’est pas un aperçu du maillage importé. Après la génération de l’avatar, contrôlez le résultat dans le projet et lors de la préparation du calcul.

## Après l’assistant

- L’avatar déformable apparaît dans **Avatars**.
- Les contacteurs peuvent être vérifiés ou modifiés dans **Contactors**.
- La loi et les paires d’interaction se configurent dans **Contact** et **Visibility**.
- Pour appliquer des conditions, utilisez **DOF**.

Voir également [Contacteurs](contactors.md), [Tables de visibilité](visibility.md) et [Conditions aux limites](dof.md).
