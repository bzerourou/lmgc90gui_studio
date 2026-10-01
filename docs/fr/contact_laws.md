# Lois de contact

Une loi de contact décrit la réponse mécanique d’une paire de contacteurs. La table de visibilité associe ensuite les formes et couleurs qui peuvent interagir à une loi nommée.

## Créer une loi

1. Ouvrez **Onglets → Ouvrir → Contact** (`Ctrl+7`).
2. Saisissez **Name** (maximum cinq caractères) ou gardez la proposition disponible.
3. Sélectionnez **Law type**.
4. Complétez les champs de **Parameters**. Ils changent selon la loi sélectionnée.
5. Cliquez sur **Add** et vérifiez que la loi apparaît dans la liste.

Les lois courantes à contact frottant, telles que `IQS_CLB`, présentent un coefficient `fric`. D’autres lois peuvent présenter des paramètres de cohésion, de restitution, de raideur, de précontrainte ou de rupture ; seuls les paramètres requis par le type courant sont affichés.

## Types proposés

Les types exposés par la version actuelle comprennent notamment :

- lois de contact rigide-rigide : `IQS_CLB`, `IQS_CLB_g0`, `IQS_DS_CLB`, `IQS_MOHR_DS_CLB`, `IQS_MAC_CZM`, `RST_CLB` ;
- lois rigide-déformable : `GAP_SGR_CLB`, `GAP_SGR_CLB_g0`, `GAP_MOHR_DS_CLB`, `MAC_CZM`, `MAL_CZM` ;
- liaisons : `ELASTIC_WIRE`, `BRITTLE_ELASTIC_WIRE`, `ELASTIC_ROD`, `VOIGT_ROD` ;
- couplages ou répulsion : `COUPLED_DOF`, `NORMAL_COUPLED_DOF`, `ELASTIC_REPELL_CLB`.

La compatibilité entre loi et paire de contacteurs dépend du type de simulation. Si le choix de paramètres semble inadapté, consultez la documentation LMGC90 de la loi avant le calcul.

## Exemples de paramètres fréquemment affichés

| Famille | Paramètres possibles dans le formulaire |
|---|---|
| Coulomb (`IQS_CLB`) | `fric` |
| Variante avec jeu initial (`IQS_CLB_g0`) | `fric`, `g0` |
| Loi discrète (`IQS_DS_CLB`) | `fric`, `Rest` |
| Mohr-Coulomb discret | `fric`, `cohes`, éventuellement `Rest` selon la loi |
| Zone cohésive | `W`, `dn`, `dt` |
| Fil / barre élastique | `stiffness`, `prestrain` ou `force_max` selon la loi |
| Barre de Voigt | `stiffness`, `viscosity` |

Les noms exacts visibles dans **Parameters** sont transmis à pylmgc90. Ne copiez pas le paramètre d’une loi dans une autre si celui-ci n’est pas proposé.

## Modifier ou supprimer une loi

1. Cliquez sur sa ligne dans la liste.
2. Vérifiez **Name**, **Law type** et les paramètres rechargés.
3. Modifiez-les puis cliquez sur **Update**.
4. Pour supprimer la loi, sélectionnez-la et cliquez sur **Delete**.
5. Utilisez **Clear form** pour désélectionner l’entrée et préparer une autre loi.

Une loi référencée par une table de visibilité ne peut plus être trouvée par cette table si elle est renommée ou supprimée. Après toute modification, ouvrez **Visibility** et vérifiez les références.

## Associer la loi à des contacteurs

1. Vérifiez que les avatars ont leurs formes de contact dans **Contactors** si nécessaire.
2. Créez ou sélectionnez une loi dans **Contact**.
3. Ouvrez **Visibility**.
4. Choisissez les corps, contacteurs et couleurs candidat/antagoniste.
5. Sélectionnez le nom exact de la loi et réglez **Alert**.
6. Cliquez sur **Add**, puis utilisez **Vérifier** pour voir les lois qui ne sont pas référencées ou les références inconnues.

La création d’une loi seule ne l’applique à aucun contact. La table de visibilité est l’étape qui la rattache aux paires concernées.
