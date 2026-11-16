# Bibliothèque d'exemples

La bibliothèque fournit des scènes de démonstration que l'on peut charger
dans un projet. L'application affiche les entrées disponibles, leurs
descriptions, dimensions et catégories ; cette liste évolue avec les exemples.

## Charger un exemple

1. Ouvrez la bibliothèque d'exemples depuis le menu **Examples**.
2. Sélectionnez une entrée pour consulter sa description et sa dimension,
   puis choisissez **Load**.
3. Choisissez de remplacer le projet courant ou d'y ajouter la scène.
4. Inspectez le projet obtenu et enregistrez-le pour conserver votre travail.

**Replace** crée un nouveau projet pour l'exemple. Confirmez d'abord toute
demande concernant les modifications non enregistrées. **Append to project**
conserve le projet courant et son historique des commandes ; l'exemple doit
avoir la même dimension que le projet. L'ajout utilise la politique de fusion :
vérifiez les noms et groupes ensuite.

## Implémentation du catalogue

La géométrie des scènes et la construction du projet appartiennent à
`lmgc90_core`, pas à un dialogue ou un widget. Un constructeur de scène est un
appelable de forme `Callable[[Project], None]` ; il utilise les entités et API
core et ne construit aucun objet pylmgc90 ou Qt.

Le registre core `lmgc90_core.scenes.SCENE_BUILDERS` associe les IDs des
scènes à leurs constructeurs. Le registre GUI
`lmgc90_gui.examples.EXAMPLES` contient les métadonnées `ExampleSpec` (ID,
titre, catégorie, description, dimension, difficulté, tags) et une référence
au constructeur. L'interface vérifie que chaque entrée pointe vers la
fonction enregistrée sous le même ID.

Pour ajouter un exemple :

1. Implémentez et exportez le constructeur dans `lmgc90_core/scenes/`, puis
   enregistrez son ID dans `SCENE_BUILDERS`.
2. Ajoutez le `ExampleSpec` correspondant dans `lmgc90_gui/examples/`.
3. Gardez le même ID dans les métadonnées et le registre des constructeurs.
4. Ajoutez ou mettez à jour les tests ciblés de scène/export.

`ProjectController.apply_scene` exécute le constructeur sur un `Project`.
Il résout les configurations granulométriques en attente et notifie ensuite
l'interface. Le choix remplacer/ajouter appartient à l'interface de
chargement, pas au constructeur de scène.
