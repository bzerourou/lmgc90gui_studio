# Avatar groups

The **Groups** tab lets you gather several avatars under a single name. A group can serve as a target for DOF operations, post-processing extractions and the 3D visualisation filter.

![](../captures/groups.png)

## Create a group

1. Open **Tabs → Open → Groups**.
2. In **Members**, select the avatars to include. Multi-selection is enabled; click a selected avatar to deselect it.
3. Enter a name in the **group name** field. The application proposes a unique name if the field is empty.
4. Click **New / Update**.
5. The group appears under **Existing groups** with the member count.

The members list identifies avatars by a short identifier, their type and their centre. It does not depend on the avatar's position in the list.

## Edit a group

1. Select the group under **Existing groups**.
2. Check the selected avatars in **Members**.
3. Add or remove members by selection.
4. Click **New / Update** to save the new composition under that name.

An existing name therefore updates the corresponding group. Check the name before confirming to avoid replacing the composition of an intended group.

## Delete a group

1. Select the group under **Existing groups**.
2. Click **Delete group**.

Deletion removes the group, not the avatars that compose it. Operations or commands that targeted that name are not automatically redirected to another group.

## Groups created by other tools

Masonry assistants and some parametric or granulometric generations may register a group automatically. It appears under **Existing groups** and can then be targeted in the appropriate tabs.

Manual groups contain individual avatars. Massive SoA populations are not a selection of avatar rows in this panel; they are identified and managed from **Granulo**.

## Use a group

- **DOF**: choose `group` in **Target type**, then select the group name in **Target value**.
- **Post-pro**: choose `group` in **Target type**, then indicate the targeted group.
- **3D Visualisation**: select the name in the group filter to show only its avatars.

If a group is not offered in a tab, first check that it contains avatars and that the list was refreshed after its creation.
