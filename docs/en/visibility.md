# Visibility tables

A visibility table (see-table) declares a contactor pair that may interact, the colours to consider, the contact law to use and the alert distance. It creates neither avatar, contactor nor law.

![](../captures/visibility.png)

## Create a table

1. First create the avatars and populations that should interact.
2. Ensure their materials and models are defined and, if needed, that their contactors are in **Contactors**.
3. Create a law in **Contact**.
4. Open **Tabs → Open → Visibility** (`Ctrl+8`).
5. In **Candidate body**, choose the mobile body type. Choices follow the project dimension and present body types.
6. Choose **Candidate shape (mobile)**. The list prioritises real contactors of bodies compatible with the candidate role.
7. Choose **Candidate color**. For the selected shape, the application proposes colours actually associated with those contactors.
8. Choose **Antagonist body**, **Antagonist shape (obstacle)** and **Antagonist color** the same way.
9. Select **Law (behav)** among project laws.
10. Set **Alert**, the detection distance before contact, in units consistent with the geometry.
11. Click **Add**.

The form list is chained: changing the body updates shapes, and changing the shape updates colours. Shape and colour lists remain editable for specialised cases. If a free combination matches no project contactor, the application asks for confirmation before saving. Each colour code must contain exactly five characters.

## Common rules

### Grains among themselves

1. Check the colour and contactor of the grains (often `DISKx` in 2D or `SPHER` in 3D).
2. Click **Grains↔grains** to prefill a homogeneous pair.
3. Check colour, law and alert distance before clicking **Add**.

### Grains against a wall or the ground

1. Click **Grains↔ground** to propose a usual mobile contactor and antagonist contactor.
2. Select the grain colour and the wall colour from scene colours.
3. Check body, law and **Alert**, then add the table.

Presets fill fields; they do not replace checking the shapes and colours actually used in the project.

## Edit, delete and refresh

- To edit a table, select its row, correct the form then click **Update**.
- To delete it, select it then click **Delete**.
- **Lists** reloads proposals after modifying avatars, contactors or their colours.
- **Clear form** deselects the current row.
- **Link A ↔ B** opens a compact dialog to link two colours/groups. It uses the same shape and colour proposals.

A table does not automatically create the law; if **Law (behav)** points to an unknown name, verification reports it.

## Check the configuration

1. Click **Verify**.
2. Read the warnings: avatar colour without a table, never-referenced law, unknown law name, or no table while the scene contains bodies.
3. Fix each association in **Visibility**, **Contact** or **Contactors** as appropriate.
4. Run verification again.

This check is a consistency diagnosis of colours and law names. It does not prove that all detectors or solver parameters are suitable; also check **Compute** before the computation.

## Understanding body types

- `RBDY2`: 2D rigid bodies.
- `RBDY3`: 3D rigid bodies.
- `MAILx`: meshed deformable bodies.
- `MBS2D` and `MBS3D`: multicorps body families when relevant.

Proposed shapes depend on dimension, avatar type and actually configured contactors. For a meshed avatar, for example, edge contactors must be defined in **Contactors** or in the mesh assistant before building the table.
