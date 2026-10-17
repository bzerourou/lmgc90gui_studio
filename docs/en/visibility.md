# Visibility tables

A visibility table (see-table) declares a contactor pair that may interact, the colours to consider, the contact law to use and the alert distance. It creates neither avatar, nor contactor, nor law.

![](../captures/visibility.png)

## Create a table

1. First create the avatars and populations that must interact.
2. Ensure their materials and models are defined and, if needed, that their contactors are in **Contactors**.
3. Create a law in **Contact**.
4. Open **Tabs → Open → Visibility** (`Ctrl+8`).
5. In **Candidate body**, choose the mobile body type. Choices follow the project dimension and the body types present.
6. Choose **Candidate shape (mobile)**. The list prioritises real contactors of bodies compatible with the candidate role.
7. Choose **Candidate colour**. For the selected shape, the application offers colours actually associated with those contactors.
8. Choose **Antagonist body**, **Antagonist shape (obstacle)** and **Antagonist colour** in the same way.
9. Select **Law (behav)** among the project laws.
10. Set **Alert**, the detection distance before contact, in units consistent with the geometry.
11. Click **Add**.

The form list is chained: changing the body updates the shapes, and changing the shape updates the colours. Shape and colour lists remain editable to allow specialised cases. If a free combination matches no contactor in the project, the application asks for confirmation before saving. Each colour code must contain exactly five characters.

## Common rules

### Grains among themselves

1. Check the colour and contactor of the grains (often `DISKx` in 2D or `SPHER` in 3D).
2. Click **Grains↔grains** to prefill a homogeneous pair.
3. Check the colour, law and alert distance before clicking **Add**.

### Grains against a wall or the ground

1. Click **Grains↔ground** to propose a usual mobile contactor and antagonist contactor.
2. Select the grain colour and the wall colour from the scene colours.
3. Check the body, law and **Alert**, then add the table.

Presets fill fields; they do not replace checking the shapes and colours actually used in the project.

## Edit, delete and refresh

- To edit a table, select its row, correct the form then click **Update**.
- To delete it, select it then click **Delete**.
- **Lists** reloads the suggestions after changing avatars, contactors or their colours.
- **Clear form** deselects the current row.
- **Link A ↔ B** opens a compact dialog to link two colours/groups. It uses the same shape and colour suggestions.

A table does not automatically create the law; if **Law (behav)** points to an unknown name, the check reports it.

## Check the configuration

1. Click **Check**.
2. Read the warnings: avatar colour without a table, law never referenced, unknown law name, or no table while the scene contains bodies.
3. Fix each association in **Visibility**, **Contact** or **Contactors** as appropriate.
4. Run the check again.

This check is a consistency diagnosis of colours and law names. It does not prove that all detectors or solver parameters are suitable; also check **Compute** before running.

## Understand body types

- `RBDY2`: 2D rigid bodies.
- `RBDY3`: 3D rigid bodies.
- `MAILx`: meshed deformable bodies.
- `MBS2D` and `MBS3D`: multicorp body families offered when relevant.

Offered shapes depend on the dimension, avatar type and contactors actually configured. For a meshed avatar, for example, edge contactors must be defined in **Contactors** or in the mesh wizard before building the table.
