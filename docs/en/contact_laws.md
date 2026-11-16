# Contact laws

A contact law describes the mechanical response of a contactor pair. The visibility table then associates the shapes and colours that can interact with a named law.

![](../captures/contacts.png)

## Create a law

1. Open **Tabs → Open → Contact** (`Ctrl+7`).
2. Enter **Name** (maximum five characters) or keep the suggested name.
3. Select **Law type**.
4. Fill in the **Parameters** fields. They change according to the selected law.
5. Click **Add** and check that the law appears in the list.

The fields shown come from the compatibility schema for the selected law. A field without a default is required; fields with a default are pre-filled. Use the family selector to filter the list without removing access to other laws. Parameters are passed using their exact LMGC90 names and must be chosen for the physical problem.

## Fallback law and parameter catalogue

The table below documents the 53 entries in the core `ContactLawType`
fallback catalog and their fallback parameter schemas. When compatibility
data for the installed pylmgc90 version is available, the application uses
that data for the law list, families, and parameter fields instead; the
runtime list can therefore differ. The family headings describe the core
fallback grouping. Consult the LMGC90 documentation for physical assumptions
and valid parameter ranges.

### Rigid / rigid

| Law | Fallback parameter fields |
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
| `IQS_STICK` | none |
| `IQS_CLB_nosldt` | `fric`, `dt__` |
| `IQS_CLB_RGR` | `fric`, `ToverH`, `gtol` |
| `IQS_EXPO_CZM_P` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2`, `mu_g`, `eta` |
| `IQS_EXPO_CZM_SPRING_P` | `dyfr`, `stfr`, `cn`, `ct`, `s1`, `s2`, `G1`, `G2`, `mu_g`, `eta`, `k1`, `k2` |

### Any / deformable (`any/defo`)

| Law | Fallback parameter fields |
|---|---|
| `GAP_SGR_CLB`, `GAP_SGR_CLB_g0`, `VEL_SGR_CLB` | `fric` |
| `GAP_SGR_STICK` | none |
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

| Law | Fallback parameter fields |
|---|---|
| `ELASTIC_WIRE`, `ELASTIC_ROD` | `stiffness`, `prestrain` |
| `BRITTLE_ELASTIC_WIRE` | `stiffness`, `prestrain`, `Fmax` |
| `VOIGT_ROD` | `stiffness`, `prestrain`, `viscosity` |
| `NARD_ROD` | `E`, `nu`, `s1`, `s2` |

### Any / any

| Law | Fallback parameter fields |
|---|---|
| `COUPLED_DOF`, `NORMAL_COUPLED_DOF` | none |
| `ELASTIC_REPELL_CLB`, `ELASTIC_REPELL_CLB_g0`, `ELASTIC_REPELL_CLB_adapt` | `stiffness`, `fric` |
| `VISCO_ELASTIC_REPELL_CLB` | `stiffness`, `viscosity`, `fric` |

Laws grouped on the same row share the same fallback options. Parameter names are case-sensitive (`Wthk`, `Fmax`, `Gc1`, etc.) and must be preserved exactly.

## Edit, delete and associate a law

Select a law in the list to reload its parameters, then choose **Update** to save changes. **Delete** removes it and **Clear form** prepares a new law. Renaming or deleting a law can invalidate visibility-table references, so check them in **Visibility**.

Creating a law does not apply it to any contact. In **Visibility**, choose the candidate/antagonist bodies, contactors and colours, associate the exact law name, and set **Alert**.
