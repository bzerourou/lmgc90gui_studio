# Découverte de l'interface graphique
LMGC90_GUI est une interface graphique moderne conçue pour faciliter la création de modèles numériques avec le module **pre** (pré-processeur) de **LMGC90**.

Il est également possible de configurer et lancer vos calculs directement depuis LMGC90_GUI via le module **chipy**.

L'interface est organisée de manière claire et ergonomique pour accompagner l'utilisateur du début à la fin du processus de modélisation : création des éléments, conditions aux limites, post-traitement, génération des fichiers et enfin lancement des calculs.

La vidéo suivante présente une vue d'ensemble des différentes parties de l'interface.

[![Introduction LMGC90_GUI](https://img.youtube.com/vi/2lVIGg3VboA/0.jpg)](https://www.youtube.com/watch?v=WSS62MTns1w)


## Fenêtre principale

![Vue globale de l'interface](../captures/interface_sections.png)

L'interface est divisée en **Six zones principales** :

1. **Menu**
2. **Barre d'outils** (en haut)
3. **Arbre du modèle** (à gauche)
4. **Onglets de création** (centre)
5. **Histrorique des commandes** (à droite)
6. **Barre d'état** (en bas)

La **palette des commandes**, est accessible dans la **barre d'outills** ou avec le raccourci clavier `ctrl+K`.

![Palette des commandes](../captures/palette_commandes.png)


---

## 1. Menu

### 1.1 Fichier

| Action | Raccourci | Description |
|--------|-----------|-------------|
| **Nouveau** | `Ctrl+N` | Crée un nouveau projet. Une boîte de dialogue s'ouvre pour saisir la dimension et le nom du projet. |
| **Ouvrir** | `Ctrl+O` | Ouvre un projet existant. Une boîte de dialogue permet de naviguer jusqu'au fichier `.lmgc90` du projet. |
| **Sauvegarder** | `Ctrl+S` | Sauvegarde le projet courant à son emplacement actuel. |
| **Sauvegarder sous…** | `Ctrl+Shift+S` | Sauvegarde le projet sous un nouveau nom ou dans un nouvel emplacement. |
| **Quitter** | `Ctrl+Q` | Ferme l'application. |
 
**Nouveau projet**

Cliquez sur le bouton **Nouveau** de la barre d'outils, ou utilisez le menu **Fichier → Nouveau**, ou appuyez sur `Ctrl+N`. Une boîte de dialogue s'ouvre pour renseigner la dimension puis nom du projet

  ![](../captures/titre_projet.png)

**Ouvrir un projet**
 
Cliquez sur le bouton **Ouvrir** de la barre d'outils, utilisez le menu **Fichier → Ouvrir**, ou appuyez sur `Ctrl+O`. Il vous suffira ensuite de spécifier le chemin et le nom de votre projet

  ![](../captures/ouvrir_projet.png)

**Sauvegarder**
  Sert à sauvegarder vos projets dans votre disque dur, cliquez sur le bouton **sauvegarder** de la barre d'outils, ou de cliquez sur le menu **Fichier-> Sauvegarder**, ou avec le raccourci clavier `Ctrl+S`,

---


#### 1.2 Projet

**Définir la dimension** 
Afin de rendre la dimension la même dans tout votre projet vous pouvez cliquer sur **Projet-> définir la dimension**
![](../captures/dimension.png)
 

#### 1.3 Edition 

| Action | Raccourci | Description |
|-----------|-----------|-------------|
| **Annuler** |  `Ctrl+Z` |  Annuler une action. |
| **Rétablir** |  `Ctrl+Y`| Rétablir l'action anullée. |



#### 1.4 Outils

| Action | Raccourci | Description |
|-----------|-----------|-------------|
| **Générer pre.py** | — | Génère votre script modèle (pre.py). |
| **générer command.py** | — | Génère votre script calcul (command.py). |
| **Exporter tout** | — | Exporte scripts modèle/calcul et DATBOX |
| **Pipeline** | — | Génère votre script sbatch pour une machine HPC |
| **Assistant déformable** | `Ctrl+Shift+D` | Guide la création ou l'importation d'éléments déformables (maillages rectangles, disques, sphères, cylindres ou fichiers externes `.msh` / `.geo`, etc.).
| **Assistant maçonnerie** | `Ctrl+Shift+M` | Spécialisé dans la création d'empilements de briques 2D et 3D (`brick2D` / `brick3D`) selon différents appareillages (standard, running bond, paneresse simple, paneresse double, etc.). |
| **Variables dynamiques** | `Ctrl+V` | Ouvre une boîte de dialogue permettant de définir des variables réutilisables dans les champs numériques de l'interface (rayon, espacement, offset, etc.). C'est également une fenêtre d'inspection des propriétés des objets LMGC90 présents en mémoire. Voir la page [Variables dynamiques](dynam_variables.md). |
| **visuAvatars (pylmgc90)** | — | Permet de visualiser votre modèle avec la fonction native de LMGC90 ``visuAvatars``
| **Préférences** | `Ctrl+,` | Ouvre la boîte de dialogue de configuration de l'application. Voir section [Préférences](#5-préférences). |

> **Remarque :** les assistants peuvent être relancés à tout moment pendant la session. Chaque exécution ajoute les éléments générés à la suite du projet existant, sans effacer ce qui a été créé auparavant. 
La duplication des éléments qui portent le même nom entraîne des erreurs, pensez à nommer différemment vos éléments.

---

#### 1.5 Calcul
 
| Action | Raccourci | Description |
|--------|-----------|-------------|
| **Générer DATBOX et scripts** | `Ctrl+F5` | Génère le DATBOX et les scripts modèle/calcul  |
| **Lancer calcul** | `F5` | Ouvrel'onglet calcul et lance le calcul chipy directement depuis l'interface, dans un processus séparé pour ne pas bloquer l'interface. |
| **Journal de l'application** | `F7` | Affiche le journal interne de LMGC90_GUI : erreurs non gérées, avertissements Python, appels pylmgc90 échoués. Utile pour diagnostiquer les problèmes qui ne génèrent pas de message visible dans l'interface. |
  
![](../captures/journal.png)

---

#### 1.6 Onglets
 
| Action | Raccourci | Description |
|--------|-----------|-------------|
| **Ouvrir** | — | Ouvre un onglet spécifique parmi la liste complète. Voir section [Onglets de création](#4-onglets-de-création-zone-centrale). |
| **Fermer les autres** | — | Ferme tous les onglets ouverts sauf l'onglet actif. |
| **Fermer tous (sauf essentiels)** | — | Ferme tous les onglets non essentiels. |
| **Onglets par défaut** | `Ctrl+Alt+D` | Restaure la disposition d'onglets par défaut. |
 
 ---

#### 1.7 Exemples 

Ce menu contient une seule action qui est **Bibliothèque d'exemples**, elle ouvre une boite de dialogue dans laquelles vous pouvez parcourir plusieurs exemples sous sept catégories. La sélection d'un exemple charge les détails de cet exemple sur l'onglet de droite. 

![](../captures/biblio_exemples.png)

Afin de charger un exemple, il vous suffit simplement donc de le sélectionner et cliquer sur le bouton **Charger**, dans mon cas je vais charger l'exemple `Corps déformable sur sol rigide`, un nouvelle boite de dialogue s'ouvrira afin de **replacer**, **d'ajouter au projet** qui conduira à des éléments en double ou **d'annuler** l'action.

![](../captures/exemple_capture.png)

---
 
#### 1.8 Aide
 
| Action | Description |
|--------|-------------|
| **Palette des commandes** | Ouvre la palette des commandes. |
| **À propos** | Affiche les informations sur la version de LMGC90_GUI et les dépendances. |
| **Aide en ligne** | Ouvre la documentation en ligne dans le navigateur par défaut. |
 
---
 
### 2. Barre d'outils
 
La barre d'outils regroupe les actions les plus fréquentes pour un accès rapide :

![](../captures/barre_outils.png)

 
| Bouton | Équivalent menu |
|--------|----------------|
| **Nouveau**  | Fichier → Nouveau |
| **Ouvrir**  | Fichier → Ouvrir |
| **Lancer le calcul** | calcul → Lancer le calcul
| **Sauvegarder**  | Fichier → Sauvegarder |
| **Générer DATBOX/scripts** | Calcul → Générer DATBOX/scripts | 
| **Variables dynamiques** | Outils → Variables dynamiques  |
| **Palette des commandes** | Aide → Palette des commandes  |
 
---

### 3. Arbre du modèle (à gauche)
 
Zone fixe affichant l'**arborescence du modèle**. Elle se met à jour automatiquement après chaque création, modification ou suppression d'élément.

![](../captures/model_tree.png)

 
#### Sections affichées
 
| Section | Contenu |
|---------|---------|
| **Matériaux** | Liste de tous les matériaux définis dans le projet. |
| **Modèles** | Liste de tous les modèles éléments finis (physique, élément, dimension). |
| **Avatars (AOS)** | Liste de tous les corps du projet : rigides, vides, déformables, Boucle, ForLoop, etc. |
| **Population d'avatars (SOA)** | Liste la granulométrie ou les assistants . |
| **Lois de contact** | Lois de comportement de contact définies (frottement, cohésion, rigidité). |
| **Tables de visibilité** | Règles de visibilité entre avatars pendant le calcul. |
| **DOF** | Liste les CL sur les avatars ou groupes d'avatars. |
| **Groupes** | Liste les groupes d'avatars. |
 
---

### 4. Onglets de création (zone centrale)
 
Zone principale de travail. Chaque onglet est dédié à une étape de modélisation. Pour ouvrir un onglet, utilisez le menu **Onglets → Ouvrir** et choisissez l'onglet souhaité.

![](../captures/onglets.png)

| Onglet | Raccourci | Description |
|--------|-----------|-------------|
| **Matériau** | `Ctrl+1` | Création et gestion des matériaux (RIGID, ELAS, ELAS_PLAS, THERMO_ELAS, PORO_ELAS, etc.). |
| **Modèle** | `Ctrl+2` | Définition des modèles physiques et éléments finis (MECAx, THERx, POROx, MULTI). |
| **Avatar** | `Ctrl+3` | Création de corps rigides standards : disque, jonc, polygone, mur rugueux, sphère, cylindre, polyèdre, etc. |
| **Boucles** | `Ctrl+4` | Génération paramétrique de séries d'avatars : cercle, grille, ligne, spirale ou placement manuel. |
| **ForLoop** | `Ctrl+5` | Crée des boucles For sur vos éléments : matériaux, modèles, avatars, DOF, etc. |
| **Granulométrie** | `Ctrl+6` | Génération de dépôts avec distribution statistique des rayons et dépôt gravitaire. |
| **Contact** | `Ctrl+7` | Définition des lois de comportement de contact (frottement Coulomb, cohésion, rigidité normale et tangentielle). |
| **Visibilité** | `Ctrl+8` | Création de tables de visibilité avec lesquels intéragissent les avatars pendant le calcul. |
| **DOF** | `Ctrl+9` | Conditions aux limites : translations imposées, rotations bloquées, vitesses imposées, couplages de degrés de liberté. |
| **Postpro** | — | Configuration des commandes de post-traitement : bilan énergétique, suivi de corps, extraction de champs. |
| **Visualisation 3D** | — | Affichage interactif des avatars du modèle avec modes de navigation, sélection et mesure. |
| **Groupes** | — | Paramétrer vos groupes d'avatars. |
| **Contacteurs** | — | Permet d'ajouter/supprimer des contacteurs pour vos avatars. |
| **Assistant déformables** | — | Assisant pour la création/importation des éléments déformables. |
| **Assistant maçonnerie** | — | Assistant pour la création et configuration d'éléments de maçonnerie. |

> **Raccourcis clavier :** les touches `Ctrl+1` à `Ctrl+9` ouvrent directement les neuf premiers onglets de la liste.
 
---

### 5. Zone historique des commandes (à droite)
 
Zone dédiée à la gestion de l'historique des commandes.

![](../captures/historique.png)

---
 
### 6. Barre d'état (en bas)
 
Bande horizontale en bas de la fenêtre affichant des messages contextuels sur les opérations en cours : création d'un avatar, génération d'un script, résultat d'une mesure dans le viewer 3D, erreur de validation, etc.

![](../captures/barre_etat.png)

---

### Modes interactifs du viewer 3D
 
| Mode | Description |
|------|-------------|
| **🖱️ Navigation** | Mode par défaut : rotation (clic gauche + glisser), zoom (molette), panoramique (clic droit + glisser). |
| **👆 Sélection** | Clic sur un avatar pour le mettre en évidence (surlignage jaune) et afficher ses informations dans la barre d'état. |
| **📏 Règle** | Mesure de distance : cliquer sur un premier point (A) puis un second point (B) pour afficher la distance en mètres. |
 
Les vues rapides **XY**, **XZ**, **YZ** et **Iso** sont accessibles depuis la barre d'outils du viewer.
 
---


### Préférences

Accessible via **Outils → Préférences** ou le raccourci `Ctrl+,`. La boîte de dialogue de préférences regroupe les paramètres de configuration de l'application.

![](../captures/preferences.png)

| Paramètre | Description |
|-----------|-------------|
| **Calcul** | Contient les valeurs de calculs par défauts |
| **Chemins** | Chemin par défaut utilisé lors de l'ouverture et de la sauvegarde des projets.  |
| **Sauvegarde** | Options pour activer la sauvegarde automatique à intervalles réguliers et à la fermeture de l'application. |
| **Performances** | Active ou désactive l'affichage des avatars dans l'arbre du modèle et dans le tableau de l'onglet Avatar. |

---

## Résumé des raccourcis clavier
 
| Raccourci | Action |
|-----------|--------|
| `Ctrl+N` | Nouveau projet |
| `Ctrl+O` | Ouvrir un projet |
| `Ctrl+S` | Sauvegarder |
| `Ctrl+Shift+S` | Sauvegarder sous… |
| `Ctrl+Q` | Quitter |
| `Ctrl+Shift+N` | Assistant de configuration de projet |
| `Ctrl+Shift+G` | Assistant de granulométrie pylmgc90 |
| `Ctrl+Shift+D` | Assistant de déformable |
| `Ctrl+Shift+M` | Assistant de maçonnerie |
| `Ctrl+V` | Variables dynamiques |
| `Ctrl+,` | Préférences |
| `Ctrl+F5` | Paramètres de calcul |
| `F5` | Lancer le calcul |
| `F6` | Voir les logs LMGC90 |
| `F7` | Journal de l'application |
| `Ctrl+Alt+D` | Onglets par défaut |
| `Ctrl+1` … `Ctrl+9` | Ouvrir l'onglet correspondant |
| `Ctrl+K` | Ouvrir la palette des commandes |
 
---

 
LMGC90_GUI est conçue pour être **intuitive** et **entièrement visuelle**, tout en conservant une compatibilité totale avec les scripts Python traditionnels de LMGC90.


Pour apprendre les opérations spécifiques, consultez les chapitres de [l’index français](overview.md).
