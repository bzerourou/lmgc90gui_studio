# Dynamic variables

Dynamic variables store reusable expressions in numeric fields of the interface that support expressions. The dialog shows their expression, resolved value and type.

![](../captures/variables.png)

## Add a variable

1. Open **Tools → Dynamic variables…** (`Ctrl+V`).
2. Enter a **Name** that is a valid identifier, e.g. `r_min` or `thickness` (no spaces and not starting with a digit).
3. Enter the **Expression**, e.g. `0.05` or `width + joint`.
4. Check **Preview**. The dialog shows the resulting value or a resolution error.
5. Click **Add / Update**.
6. Verify the expression, value and type in the table.

## Edit, refresh or delete

- Click a table row to load the name and expression into the form, then click **Add / Update** to save the change.
- Click **Refresh** to recompute displayed values.
- Select a row or type its name, then click **Delete** to remove the variable.
- Click **Close** to leave the dialog.

Expressions are evaluated in the order of project variables; an expression may rely on a previously defined variable. An unknown or circular reference triggers a preview error.

## Use a variable in the scene

1. Define the variable in the dialog.
2. Open a tab that accepts numeric expressions, e.g. **Avatars**.
3. Enter the variable name in a numeric field, e.g. a radius or coordinate.
4. Confirm creation or modification and fix any reported error.

Example expressions:

| Expression | Possible use |
|---|---|
| `0.05` | Fixed radius or length. |
| `diameter / 2` | Radius derived from a previously defined dimension. |
| `width + joint` | Distance composed of project parameters. |

> **Note:** The dialog uses a restricted evaluator for allowed expressions. It is not a general Python interpreter: do not rely on access to all Python modules or object methods.
