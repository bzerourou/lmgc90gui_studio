# Assistant de maçonnerie

L’assistant **Maçonnerie** construit un assemblage de briques polygonales et peut créer le groupe, la loi de contact et la table de visibilité associés. Ouvrez-le depuis **Tools → Assistant Maçonnerie…** (`Ctrl+Shift+M`) ou depuis l’onglet **Masonry**.

## Suivre l’assistant

1. Dans **Introduction**, cliquez sur **Suivant**.
2. **Dimension** : choisissez 2D ou 3D. Les motifs paneresse sont réservés à la 3D.
3. **Matériau** : créez un matériau `RIGID` avec sa densité ou sélectionnez un matériau existant.
4. **Modèle** : créez un modèle rigide ou réutilisez-en un de dimension compatible (`Rxx2D` en 2D, `Rxx3D` en 3D).
5. **Dimensions de la brique** : indiquez le nom (cinq caractères maximum), `lx`, `ly` et la profondeur `lz` en 3D.
6. **Appareil et disposition** : choisissez le motif, les courses, les colonnes, la largeur du joint, les offsets et la couleur.
7. Choisissez si vous souhaitez enregistrer un **groupe** et définissez son nom.
8. L’option **Ajouter loi IQS_CLB + see-table** est cochée par défaut. Ajustez le nom de loi et la friction, ou décochez-la si vous configurerez les interactions vous-même.
9. **Transformations** : activez **Translation globale** et renseignez `tx`, `ty`, `tz` si nécessaire. Pour dupliquer l’assemblage, activez **Copies additionnelles**, saisissez le nombre de copies et leur décalage `dx`, `dy`, `dz`.
10. **Résumé et génération** : vérifiez dimensions, matériau, modèle, motif, taille de l’assemblage, groupe, loi et transformations.
11. Cliquez sur **Générer**. Une confirmation indique le nombre de briques créées.

Les boutons **Retour**, **Suivant** et **Annuler** permettent de naviguer dans l’assistant avant la validation finale.

## Motifs disponibles

| Motif | Disposition générale |
|---|---|
| `Standard` | Décalage d’une demi-brique sur les rangs alternés ; option de demi-briques aux extrémités. |
| `Running Bond` | Décalage progressif des joints entre rangs. |
| `Stack Bond` | Joints alignés verticalement. |
| `Flemish Bond` | Alternance de briques en longueur et en boutisse. |
| `Paneresse simple (pylmgc90)` | Appareillage 3D spécialisé, options dans le groupe paneresse. |
| `Paneresse double (pylmgc90)` | Deux feuilles 3D, options dans le groupe paneresse. |

Les choix spécifiques au motif s’affichent dans l’étape de disposition : disposition paneresse, première brique, mode de longueur et option sans demi-briques.

## Limites et résultat

- La rotation pure n’est pas appliquée dans la version actuelle ; l’interface le précise à l’étape **Transformations**.
- Une nouvelle génération ajoute des briques au projet et ne remplace pas les précédentes.
- Si l’assistant crée la loi et la see-table, vérifiez la couleur et le contacteur utilisés dans **Visibility** après génération.
- Les briques sont des avatars du projet. Vous pouvez inspecter le groupe dans **Groups** et actualiser la scène dans **Visualisation 3D**.
