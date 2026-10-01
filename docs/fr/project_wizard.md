# Créer, ouvrir et organiser un projet

Cette page remplace l’ancienne procédure de l’assistant de configuration de projet : cet assistant n’est plus proposé dans l’interface actuelle. La création d’un projet se fait directement depuis **File → New**.

## Créer un projet

1. Choisissez **File → New** ou appuyez sur `Ctrl+N`.
2. Dans la boîte **New project**, choisissez la dimension `2` ou `3`.
3. Saisissez un nom puis validez. Le projet est créé dans l’application ; il n’est pas encore enregistré sur disque.
4. Choisissez **File → Save As…** (`Ctrl+Shift+S`), sélectionnez un dossier et un nom de fichier, puis enregistrez. L’extension `.lmgc90` est ajoutée si elle manque.
5. Vérifiez le nom et la dimension dans la barre d’état.

## Enregistrer et reprendre le travail

- **File → Save** (`Ctrl+S`) enregistre les modifications à l’emplacement courant.
- **File → Save As…** crée une copie sous un autre nom ou dans un autre dossier.
- **File → Open…** (`Ctrl+O`) ouvre un fichier de projet `.lmgc90`.
- **Edit → Undo** (`Ctrl+Z`) et **Edit → Redo** (`Ctrl+Y`) annulent ou rétablissent les dernières actions lorsque l’historique les permet.

Enregistrez le projet après les opérations importantes, avant de lancer un calcul et avant de charger un exemple en mode remplacement.

## Choisir et modifier la dimension

La dimension du projet détermine les éléments, avatars, contacteurs et corps proposés dans les formulaires.

1. Définissez `2` ou `3` au moment de la création.
2. Pour la modifier ensuite, choisissez **Project → Set dimension…**.
3. Sélectionnez la nouvelle dimension et lisez l’avertissement si des modèles existants ne correspondent plus.
4. Confirmez uniquement après avoir vérifié les modèles et les avatars. Le changement de dimension ne convertit pas automatiquement les objets existants.

En cas de changement majeur entre 2D et 3D, la solution la plus claire est souvent de créer un nouveau projet de la bonne dimension et d’y reconstruire ou recharger la scène appropriée.

## Première séquence de modélisation

Une fois le projet créé, le parcours usuel dans les onglets est :

1. Créer un matériau dans **Materials**.
2. Créer un modèle dans **Models**.
3. Créer un ou plusieurs corps dans **Avatars**, ou utiliser **Granulo**, **Deformable** ou **Masonry** pour une génération spécialisée.
4. Définir les lois de contact dans **Contact**, puis leurs associations dans **Visibility**.
5. Ajouter les conditions aux limites dans **DOF** et, si utile, créer des **Groups**.
6. Enregistrer le projet, configurer **Compute**, puis préparer et lancer le calcul.

Les assistants **Assistant Mesh déformable** (`Ctrl+Shift+D`) et **Assistant Maçonnerie** (`Ctrl+Shift+M`) sont disponibles depuis **Tools**. L’assistant général de configuration de projet et l’assistant Granulométrie décrits dans les anciennes pages ne font pas partie des menus actuels.

## Organisation des onglets

Utilisez **Onglets → Ouvrir** pour afficher une fonction. Les onglets Materials et Models restent ouverts comme onglets essentiels. Fermer un onglet ne supprime pas les éléments du projet.

Les neuf premiers onglets ont les raccourcis `Ctrl+1` à `Ctrl+9` dans cet ordre : Materials, Models, Avatars, Loops, ForLoop, Granulo, Contact, Visibility et DOF. **Onglets → Onglets par défaut** (`Ctrl+Alt+D`) restaure la disposition initiale.

Pour le détail des menus, panneaux et raccourcis, voir [Découverte de l’interface](interface.md). Pour les procédures de création, utilisez les chapitres spécialisés listés dans [l’index](overview.md).