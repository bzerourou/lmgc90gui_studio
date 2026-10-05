# Contact laws

A contact law describes the mechanical response of a contactor pair. The visibility table then associates the shapes and colours that may interact with a named law.

![](../captures/contacts.png)

## Create a law

1. Open **Tabs → Open → Contact** (`Ctrl+7`).
2. Enter **Name** (maximum five characters) or keep the proposed available name.
3. Select **Law type**.
4. Fill in the **Parameters** fields. They change according to the selected law.
5. Click **Add** and check that the law appears in the list.

Common frictional contact laws such as `IQS_CLB` show a `fric` coefficient. Other laws may show cohesion, restitution, stiffness, prestress or failure parameters; only the parameters required by the current type are displayed.

## Available types

Types exposed by the current version include notably:

- rigid-rigid contact laws: `IQS_CLB`, `IQS_CLB_g0`, `IQS_DS_CLB`, `IQS_MOHR_DS_CLB`, `IQS_MAC_CZM`, `RST_CLB`;
- rigid-deformable laws: `GAP_SGR_CLB`, `GAP_SGR_CLB_g0`, `GAP_MOHR_DS_CLB`, `MAC_CZM`, `MAL_CZM`;
- links: `ELASTIC_WIRE`, `BRITTLE_ELASTIC_WIRE`, `ELASTIC_ROD`, `VOIGT_ROD`;
- couplings or repulsion: `COUPLED_DOF`, `NORMAL_COUPLED_DOF`, `ELASTIC_REPELL_CLB`.

Compatibility between a law and a contactor pair depends on the simulation type. If parameter choices seem unsuitable, consult the LMGC90 documentation for the law before running the computation.

## Frequently displayed parameter examples

| Family | Possible parameters in the form |
|---|---|
| Coulomb (`IQS_CLB`) | `fric` |
| Variant with initial gap (`IQS_CLB_g0`) | `fric`, `g0` |
| Discrete law (`IQS_DS_CLB`) | `fric`, `Rest` |
| Discrete Mohr-Coulomb | `fric`, `cohes`, possibly `Rest` depending on the law |
| Cohesive zone | `W`, `dn`, `dt` |
| Elastic wire / rod | `stiffness`, `prestrain` or `force_max` depending on the law |
| Voigt rod | `stiffness`, `viscosity` |

The exact names shown under **Parameters** are passed to pylmgc90. Do not copy a parameter from one law into another if it is not offered.

## Edit or delete a law

1. Click its row in the list.
2. Check **Name**, **Law type** and the reloaded parameters.
3. Edit them then click **Update**.
4. To delete the law, select it and click **Delete**.
5. Use **Clear form** to deselect the entry and prepare another law.

A law referenced by a visibility table can no longer be found by that table if it is renamed or deleted. After any change, open **Visibility** and check the references.

## Associate the law with contactors

1. Ensure avatars have their contact shapes in **Contactors** if needed.
2. Create or select a law in **Contact**.
3. Open **Visibility**.
4. Choose the bodies, contactors and candidate/antagonist colours.
5. Select the exact law name and set **Alert**.
6. Click **Add**, then use **Verify** to see laws that are not referenced or unknown references.

Creating a law alone does not apply it to any contact. The visibility table is the step that attaches it to the relevant pairs.
