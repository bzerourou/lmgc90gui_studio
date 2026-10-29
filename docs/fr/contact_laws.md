# Lois de contact

Une loi de contact décrit la réponse mécanique d’une paire de contacteurs. La table de visibilité associe ensuite les formes et couleurs qui peuvent interagir à une loi nommée.

![](../captures/contacts.png)

## Créer une loi

1. Ouvrez **Onglets → Ouvrir → Contact** (`Ctrl+7`).
2. Saisissez **Name** (maximum cinq caractères) ou gardez la proposition disponible.
3. Sélectionnez **Law type**.
4. Complétez les champs de **Parameters**. Ils changent selon la loi sélectionnée.
5. Cliquez sur **Add** et vérifiez que la loi apparaît dans la liste.

Les champs affichés sont les options obligatoires de `pylmgc90.pre.tact_behav` pour la loi choisie. La famille permet de filtrer la liste sans masquer les autres lois. Les paramètres sont transmis avec leur nom LMGC90 exact ; ils sont numériques et doivent être renseignés selon le problème physique.

## Catalogue de lois et paramètres

Le catalogue ci-dessous correspond aux 53 lois de la version `pylmgc90` utilisée comme référence par l’application. La compatibilité des lois avec les paires de contacteurs est indiquée par famille ; vérifiez la documentation LMGC90 pour les conditions physiques et les domaines de validité des paramètres.

### Rigide / rigide

| Loi | Paramètres obligatoires |
|---|---|
| `IQS_CLB` | `fric` |
| `IQS_CLB_g0` | `fric` |
| `IQS_DS_CLB` | `dyfr`, `stfr` |
| `RST_CLB` | `rstn`, `rstt`, `fric` |
| `IQS_WET_DS_CLB`, `xQS_WET_DS_CLB` | `cohn`, `coht`, `Wthk`, `dyfr`, `stfr` |
| `IQS_MOHR_DS_CLB` | `cohn`, `coht`, `dyfr`, `stfr` |
| `IQS_MAC_CZM` | `dyfr`, `stfr`, `cn`, `ct`, `b`, `w` |
| `IQS_WET_CZM` | `cohn`, `Wthk`, `cn`, `ct`, `visc`, `w` |
| `IQS_MAL_CZM` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2` |
| `IQS_TH_CZM` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2`, `dp1`, `dp2` |
| `BRITTLE_COATING_CLB` | `fric`, `stiffness`, `Fmax`, `g0` |
| `IQS_ABP_CZM` | `dyfr`, `stfr`, `cn`, `ct`, `phi`, `s1`, `s2`, `G1`, `G2`, `du1`, `du2` |
| `IQS_EXPO_CZM` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2`, `eta` |
| `IQS_EXPO_CZM_SPRING` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2`, `eta`, `k1`, `k2` |
| `IQS_STICK` | aucun |
| `IQS_CLB_nosldt` | `fric`, `dt__` |
| `IQS_CLB_RGR` | `fric`, `ToverH`, `gtol` |
| `IQS_EXPO_CZM_P` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2`, `mu_g`, `eta` |
| `IQS_EXPO_CZM_SPRING_P` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2`, `mu_g`, `eta`, `k1`, `k2` |

### Déformable / quelconque (`any/defo`)

| Loi | Paramètres obligatoires |
|---|---|
| `GAP_SGR_CLB`, `GAP_SGR_CLB_g0`, `VEL_SGR_CLB` | `fric` |
| `GAP_SGR_STICK` | aucun |
| `GAP_SGR_CLB_nosldt` | `fric`, `dt__` |
| `preGAP_SGR_CLB` | `pgap`, `fric` |
| `GAP_MOHR_DS_CLB` | `cohn`, `coht`, `dyfr`, `stfr` |
| `MAC_CZM` | `dyfr`, `stfr`, `cn`, `ct`, `b`, `w` |
| `MAL_CZM` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2` |
| `MP_CZM` | `dyfr`, `stfr`, `cn`, `ct`, `w` |
| `MP3_CZM` | `dyfr`, `stfr`, `cn`, `ct`, `smax`, `w` |
| `MP3_CZM_THER` | `dyfr`, `stfr`, `cn`, `ct`, `smax`, `w`, `lambdas`, `lambdac` |
| `TH_CZM` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2`, `dp1`, `dp2` |
| `ABP_CZM` | `dyfr`, `stfr`, `cn`, `ct`, `phi`, `s1`, `s2`, `G1`, `G2`, `du1`, `du2` |
| `EXPO_CZM` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2`, `eta` |
| `EXPO_CZM_SPRING` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2`, `eta`, `k1`, `k2` |
| `EXPO_CZM_P` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2`, `mu_g`, `eta` |
| `EXPO_CZM_SPRING_P` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2`, `mu_g`, `eta`, `k1`, `k2` |
| `GTN_CZM`, `GTN2_CZM` | `dyfr`, `stfr`, `cn`, `ct`, `f0`, `fc`, `k`, `q1`, `q2`, `e`, `Y`, `s0`, `Kh`, `n`, `fN`, `eN`, `sN` |
| `TOSI_CZM`, `TOSI_CZM_INCRE` | `dyfr`, `stfr`, `cn`, `ct`, `f0`, `fc`, `n`, `K`, `R`, `s0`, `Q`, `Gc1`, `Gc2`, `kcoal`, `hdef`, `n_mol` |

### Point / point

| Loi | Paramètres obligatoires |
|---|---|
| `ELASTIC_WIRE`, `ELASTIC_ROD` | `stiffness`, `prestrain` |
| `BRITTLE_ELASTIC_WIRE` | `stiffness`, `prestrain`, `Fmax` |
| `VOIGT_ROD` | `stiffness`, `prestrain`, `viscosity` |
| `NARD_ROD` | `E`, `nu`, `s1`, `s2` |

### Quelconque / quelconque

| Loi | Paramètres obligatoires |
|---|---|
| `COUPLED_DOF`, `NORMAL_COUPLED_DOF` | aucun |
| `ELASTIC_REPELL_CLB`, `ELASTIC_REPELL_CLB_g0`, `ELASTIC_REPELL_CLB_adapt` | `stiffness`, `fric` |
| `VISCO_ELASTIC_REPELL_CLB` | `stiffness`, `viscosity`, `fric` |

Les paramètres partagés dans une ligne ont le même jeu d’options. Les noms sensibles à la casse (`Wthk`, `Fmax`, `Gc1`, etc.) doivent rester tels quels.

## Modifier, supprimer et associer une loi

Sélectionnez une loi dans la liste pour modifier ses paramètres, puis choisissez **Update**. **Delete** la supprime et **Clear form** prépare une nouvelle loi. Renommer ou supprimer une loi peut invalider les références des tables de visibilité : vérifiez-les dans **Visibility**.

Créer une loi ne l’applique à aucun contact. Dans **Visibility**, choisissez les corps, contacteurs et couleurs candidat/antagoniste, associez le nom exact de la loi et réglez **Alert**.
