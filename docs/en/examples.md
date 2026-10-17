# Example library

> Documentation of some examples shipped with the application, accessible via
> **Examples → Browse examples…** (`Ctrl+Shift+E`).

The library lets you browse demonstration scenes and load them into a project. It is a graphical starting point; inspect and save the project after loading.

![provided examples](../captures/biblio_exemples.png)

---

## Table of contents

1. [Overview](#1-overview)
2. [Basics](#2-basics)
   - [Falling disks 2D](#21-falling-disks-2d)
   - [Sphere stack 3D](#22-sphere-stack-3d)
3. [Structures](#3-structures)
   - [Masonry wall](#31-masonry-wall)
   - [Wall with cohesive links (CZM)](#32-wall-with-cohesive-links-czm)
4. [Mass generation](#4-mass-generation)
   - [Granulometric deposit](#41-granulometric-deposit)
   - [Geometric loop — Circle](#42-geometric-loop--circle)
5. [Advanced — Contact and mechanisms](#5-advanced--contact-and-mechanisms)
   - [Rotating drum](#51-rotating-drum)
   - [Hopper discharge](#52-hopper-discharge)
   - [Wheel/rail contact (railway)](#53-wheelrail-contact-railway)
   - [Bicycle disc brake](#54-bicycle-disc-brake)
   - [Ball bearing (2D cross-section)](#55-ball-bearing-2d-cross-section)
6. [Advanced — Deformable](#6-advanced--deformable)
   - [Deformable body on rigid ground](#61-deformable-body-on-rigid-ground)
7. [Synthesis](#7-synthesis)
   - [Composite scene](#71-composite-scene)
8. [Full summary table](#8-full-summary-table)

---

## Browse the catalogue

1. Choose **Examples → Example library…** (`Ctrl+Shift+E`).
2. Browse the list grouped by category.
3. Click an example. The right-hand panel shows its title, dimension, level, description and keywords.
4. Click **Load** to continue or **Cancel** to close without selecting an example.

> **Note:** Before choosing **Replace**, save the current project if you want to keep it. Before **Add to project**, mind names already present: collisions can prevent a correct merge.

---

## After loading

1. Check the project name and dimension in the status bar.
2. Browse the content in the **Model tree** and in the Materials, Models, Avatars, Contact and Visibility tabs.
3. Click **Refresh scene** in **3D Visualisation** to display the example avatars/populations.
4. Save the project with **File → Save As…** to keep an independent working copy.

Available scenes and their categories evolve with the application.

## 2. Basics

### 2.1 Falling disks 2D

**Dimension:** 2D · **Difficulty:** Beginner

The classic starting point: a row of rigid disks falls under gravity onto a wall.

| Element | Detail |
|---|---|
| Material | `TDURx`, RIGID, ρ = 2500 kg/m³ |
| Model | `rigid`, MECAx / Rxx2D |
| Ground | `SMOOTH_WALL` (fixed smooth wall), `l=4.0`, `h=0.1` |
| Mobile avatars | 10 `RIGID_DISK` (r = 0.1 m) via **Line** loop (`step=0.3`) |
| Contact law | `IQS_CLB`, friction = 0.3 |
| Visibility | Disk/Disk + Disk/Ground (contactors `DISKx`/`JONCx`) |

**Mechanisms illustrated:** geometric **Line** `Loop`, creation of a model avatar then automatic generation of copies via `controller.generate_loop(loop)`.

---

### 2.2 Sphere stack 3D

**Dimension:** 3D · **Difficulty:** Beginner

3×3 grid of rigid spheres stacked on a plane.

| Element | Detail |
|---|---|
| Material | `TDURx`, RIGID, ρ = 2500 kg/m³ |
| Model | `rigid`, MECAx / Rxx3D |
| Ground | `RIGID_PLAN` (`axe1=axe2=2.0`, `axe3=0.05`) |
| Avatars | 9 `RIGID_SPHERE` (r = 0.15 m), 3×3 grid, step = 0.6 m |
| Laws | `IQS_CLB`, friction = 0.3 |
| Visibility | Sphere/Sphere + Sphere/Plane (`SPHER`/`PLANx`) |

**Implementation note:** **direct** placement of spheres (Python `for` loop), because the built-in “Grid” `Loop` generator only produces 2D centres — see `core/generators.py::LoopGenerator.generate_grid`.

---

## 3. Structures

### 3.1 Masonry wall

**Dimension:** 2D · **Difficulty:** Intermediate

Wall of 8 rows × 5 columns of bricks in **Standard** bond (half-brick offset between consecutive rows).

| Element | Detail |
|---|---|
| Material | `brick`, RIGID, ρ = 1800 kg/m³ |
| Brick | `pre.brick2D("std", lx=0.20, ly=0.065)` (standard French size) |
| Representation | `EMPTY_AVATAR` with `wall_params={'l','h','brick_name'}` |
| Group | `mur_briques` (all generated avatars) |
| Contact law | `IQS_CLB`, friction = 0.6 |

**Key mechanism:** each brick is created in two steps — a real pylmgc90 object via `pre.brick2D(...).rigidBrick(...)` (added directly to `controller._bodies_container`), then a matching `Avatar(EMPTY_AVATAR)` in `state.avatars` for persistence/UI.

---

### 3.2 Wall with cohesive links (CZM)

**Dimension:** 2D · **Difficulty:** Advanced

Two rows of 6 blocks bonded with a **cohesive zone** law (strength before rupture, then degradation).

| Element | Detail |
|---|---|
| Brick | 0.25 × 0.10 m, 2 courses × 6 columns |
| Contact law | `IQS_MAC_CZM` |
| Mandatory properties | `stfr=1e10`, `dyfr=1e10`, `cn=5e6`, `ct=3e6`, `b=1.0`, `w=0.02` |

**Documented attention point in the source:** `IQS_MAC_CZM` properties must be passed via `properties={...}` and **never** as direct constructor parameters of `ContactLaw` (pitfall already encountered and fixed in `ex_deformable_drop.py`).

---

## 4. Mass generation

### 4.1 Granulometric deposit

**Dimension:** 2D · **Difficulty:** Intermediate

500 disks of random radii deposited by gravity in a box.

| Parameter | Value |
|---|---|
| Number of particles | 500 |
| Radii | [0.03, 0.08] m |
| Container | `Box2D`, `lx=4.0`, `ly=4.0` |
| Seed | 42 (reproducible) |
| Group | `depot_box` |

---

### 4.2 Geometric loop — Circle

**Dimension:** 2D · **Difficulty:** Beginner

12 disks arranged in a circle (radius 2.0 m) around a model avatar.

---

## 5. Advanced — Contact and mechanisms

### 5.1 Rotating drum

**Dimension:** 2D · **Difficulty:** Advanced

Hollow disk (`is_hollow=True`) driven at constant rotation, containing a granulometric deposit.

| Element | Detail |
|---|---|
| Drum | `RIGID_DISK`, r = 2.2 m, `is_hollow=True` → contactor `xKSID` |
| Drum DOF | translation locked (`component=[1,2]`) + driven rotation (`component=3, ct=0.5 rad/s`) |
| Internal deposit | `Drum2D`, r = 2.0 m (< drum radius), 200 particles, [0.05, 0.09] m |
| Law | `IQS_CLB`, friction = 0.45 |
| Post-pro | `COORDINATION NUMBER` |

**Key point:** the `xKSID` contactor (**inner** cylindrical wall) is the same mechanism used by the standard granulometry `Drum2D` container — see also [Ball bearing](#55-ball-bearing-2d-cross-section) which reuses the same principle for the outer ring.

---

### 5.2 Hopper discharge

**Dimension:** 2D · **Difficulty:** Advanced

V-shaped hopper built from two inclined `roughWall`s, receiving a granulometric deposit of 180 disks.

| Element | Detail |
|---|---|
| Hopper geometry | `top_width=1.6`, `bottom_width=0.45`, `height=1.2` m |
| Walls | 2× `ROUGH_WALL` + rotation `DOFOperation(operation_type="rotate", ...)` about the wall’s own centre |
| Immobilisation | **group** `imposeDrivenDof` (`hopper_walls`) |
| Deposit | `Box2D`, 180 particles, [0.04, 0.07] m |
| Post-pro | `KINETIC ENERGY` |

---

### 5.3 Wheel/rail contact (railway)

**Dimension:** 3D · **Difficulty:** Advanced

Cylindrical wheel rolling on a rail modelled as a rigid plane, with a **rail joint** segment showing a slight misalignment defect.

| Element | Detail |
|---|---|
| Wheel | `RIGID_CYLINDER`, Ø 920 mm (UIC standard), tread width 135 mm |
| Rail | `RIGID_PLAN`, length 3.0 m, head 70 mm |
| Rail joint | second `RIGID_PLAN`, 4 mm vertical defect |
| Wheel DOF | lateral guidance locked (`component=2`) + imposed longitudinal translation (`component=1, ct=1.5 m/s`) |
| Rail/joint DOF | fully immobilised (6 RBDY3 DOFs) |
| Rolling law | `IQS_CLB`, friction = 0.3 (dry steel/steel) |
| Joint impact law | `RST_CLB`, friction = 0.2, `rstn=0.3`, `rstt=0.15` |
| Post-pro | `KINETIC ENERGY`, `TORQUE EVOLUTION` (on the wheel) |

**Mechanisms illustrated:** two **distinct** contact laws applied to the same contactor-type pair (`CYLND`/`PLANx`) according to the antagonist colour — allows differentiated behaviour (continuous rolling vs localised impact) without duplicating avatars.

---

### 5.4 Bicycle disc brake

**Dimension:** 3D · **Difficulty:** Advanced

Brake disc clamped by two caliper pads; friction actually brakes the wheel.

| Element | Detail |
|---|---|
| Disc | `RIGID_CYLINDER`, Ø 160 mm, thickness 1.8 mm |
| Pads | 2× `RIGID_PLAN`, 34 × 20 × 8 mm, piston closing at 5 mm/s |
| Hub | translation + pitch/yaw locked, **spin free** |
| Initial condition | `imposeInitValue(component=6, value=ω₀)` — wheel at 25 km/h |
| Contact law | `IQS_CLB`, friction = 0.40 (semi-metallic / dry stainless) |
| Post-pro | `KINETIC ENERGY`, `DISSIPATED ENERGY`, `TORQUE EVOLUTION` |

**Physical fidelity point:** unlike a simple drive, the disc rotation is set as an **initial condition** (`imposeInitValue`) and not as a continuously imposed velocity (`imposeDrivenDof`) — otherwise pad friction would have no observable effect and the example would not represent braking.

---

### 5.5 Ball bearing (2D cross-section)

**Dimension:** 2D · **Difficulty:** Advanced

Cross-section of a type 608 deep-groove ball bearing.

| Element | Detail |
|---|---|
| Outer ring | hollow `RIGID_DISK` (`is_hollow=True`), r ≈ 9.5 mm, fixed |
| Inner ring | solid `RIGID_DISK`, r ≈ 5.0 mm, pure driven rotation (~300 rpm) |
| Balls | 7× free `RIGID_DISK` (**no imposed DOF**), seated in the gap |
| Law | `IQS_CLB`, friction = 0.05 (lubricated rolling) |
| Post-pro | `KINETIC ENERGY`, `COORDINATION NUMBER`, `VIOLATION EVOLUTION` |

---

## 6. Advanced — Deformable

### 6.1 Deformable body on rigid ground

**Dimension:** 2D · **Difficulty:** Advanced

Deformable rectangle (triangular mesh, elastic material) falling onto a rigid wall.

| Element | Detail |
|---|---|
| Deformable material | `ELAS1`, ELAS, young=70 GPa, ν=0.3 |
| Mesh | `pre.buildMesh2D("2T3", ...)`, 6×3 elements, rectangle 1.0×0.4 m |
| FE model | `femxx`, element `T3xxx` |
| Ground | rigid `SMOOTH_WALL` |
| Law | `GAP_SGR_CLB`, friction = 0.3 (rigid/deformable) |

---

## 7. Synthesis

### 7.1 Composite scene

**Dimension:** 2D · **Difficulty:** Advanced

The most complete example in the catalogue: combines almost all mechanisms in a single project.

| Category | Content |
|---|---|
| Avatars | disk, jonc, polygon (diamond), cluster, brick wall, inclined ramp |
| Materials | 3 (`brick`, `TDURx`, `steel`), different densities |
| Contact laws | `IQS_CLB` (pure friction), `RST_CLB` (restitution), `IQS_MOHR_DS_CLB` (cohesion + friction) |
| Visibility | cross tables **by colour pair** (not only same-colour) |
| Dynamic variables | 11 interdependent variables (`state.dynamic_vars`), inspectable via **Tools → Dynamic variables** after loading |

**Pedagogical interest:** shows how dynamic variables can drive the whole geometry of a scene (`site_width`, `joint_thickness`, `disk_spacing = disk_radius * spacing_factor`, …), reusing `SafeEvaluator` / `build_eval_context` exactly as a form field would in the UI.

---

## 8. Full summary table

This table lists all examples you can open/save and visualise.

| ID | Title | Dim. | Difficulty | Main tags |
|---|---|:-:|---|---|
| `falling_disks` | Falling disks 2D | 2D | Beginner | avatar, contact, loop |
| `sphere_stack` | Sphere stack 3D | 3D | Beginner | avatar, 3d |
| `masonry_wall` | Masonry wall | 2D | Intermediate | masonry, group |
| `granulo_deposit` | Granulometric deposit | 2D | Intermediate | granulo, mass |
| `circle_loop` | Geometric loop — Circle | 2D | Beginner | loop, group |
| `deformable_drop` | Deformable body on rigid ground | 2D | Advanced | deformable, fem |
| `cohesive_wall` | Wall with cohesive links (CZM) | 2D | Advanced | contact, czm |
| `dumbbell_avatar` | Composite avatar — dumbbell | 2D | Intermediate | empty_avatar, contactors |
| `for_loop_ramp` | For loop — radius ramp | 2D | Intermediate | loop, for |
| `dof_conditions` | DOF boundary conditions | 2D | Intermediate | dof, boundary_conditions |
| `couette_shear` | Couette cell shear | 2D | Advanced | granulo, couette |
| `hopper_discharge` | Hopper discharge | 2D | Advanced | factory, granulo, dof |
| `cable_pendulum` | Cable pendulum | 2D | Advanced | contact, dof, point_point |
| `deformable_impact` | Deformable impact (full contactor) | 2D | Advanced | deformable, contact |
| `l_shaped_wall` | L-structure + granulo | 2D | Advanced | masonry, granulo, dof |
| `silo_factory` | Silo factory | 2D | Advanced | factory, contact, postpro |
| `rotating_drum` | Rotating drum | 2D | Advanced | dof, granulo, rotation |
| `biaxial_compression` | Biaxial compression | 2D | Advanced | dof, granulo, mechanical_test |
| `hexagon_packing` | Hexagonal packing | 2D | Intermediate | avatar, polygon |
| `cluster_pile` | Cluster pile | 2D | Intermediate | avatar, cluster |
| `avalanche_slope` | Avalanche on inclined slope | 2D | Advanced | dof, granulo, slope |
| `wheel_rail_contact` | Wheel/rail contact (railway) | 3D | Advanced | contact, 3d, railway, dof, postpro |
| `disc_brake` | Bicycle disc brake | 3D | Advanced | contact, 3d, brake, dof, postpro, energy |
| `ball_bearing` | Ball bearing (2D cross-section) | 2D | Advanced | contact, bearing, dof, postpro |
| `composite_scene` | Composite scene — full synthesis | 2D | Advanced | synthesis, variables, contact, avatar |
