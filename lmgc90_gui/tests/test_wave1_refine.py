"""Vague 1 refined — ELAS, MULTI, rich avatars, ForLoop, law props."""
from lmgc90_core import ForLoop, pre
from lmgc90_core.types import CONTACT_LAW_PROPERTY_SCHEMA, ELEMENTS_BY_PHYSICS, MATERIAL_PROPERTY_SCHEMA
from lmgc90_gui import ProjectController


def test_schemas_present():
    assert "ELAS" in MATERIAL_PROPERTY_SCHEMA
    assert "young" in [n for n, *_ in MATERIAL_PROPERTY_SCHEMA["ELAS"]]
    assert "MULTI" in ELEMENTS_BY_PHYSICS
    assert "IQS_DS_CLB" in CONTACT_LAW_PROPERTY_SCHEMA
    expected_contact_fields = {
        "IQS_CLB_g0": ["fric"],
        "IQS_DS_CLB": ["dyfr", "stfr"],
        "IQS_MOHR_DS_CLB": ["cohn", "coht", "dyfr", "stfr"],
        "IQS_MAC_CZM": ["dyfr", "stfr", "cn", "ct", "b", "w"],
        "RST_CLB": ["rstn", "rstt", "fric"],
        "GAP_SGR_CLB_g0": ["fric"],
        "GAP_MOHR_DS_CLB": ["cohn", "coht", "dyfr", "stfr"],
        "MAC_CZM": ["dyfr", "stfr", "cn", "ct", "b", "w"],
        "MAL_CZM": ["dyfr", "stfr", "cn", "ct", "s1", "s2", "G1", "G2"],
        "BRITTLE_ELASTIC_WIRE": ["stiffness", "prestrain", "Fmax"],
    }
    for law, expected in expected_contact_fields.items():
        assert [name for name, *_ in CONTACT_LAW_PROPERTY_SCHEMA[law]] == expected


def test_elas_multi_forloop_law_props():
    ctrl = ProjectController()
    ctrl.new_project("refine", dimension=2)
    ctrl.add(pre.material(
        name="BETON", materialType="ELAS", density=2400.0,
        young=30e9, nu=0.2, elas="standard", anisotropy="isotropic",
    ))
    ctrl.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    ctrl.add(pre.model(
        name="femxx", physics="MULTI", element="T3xxx", dimension=2,
        anisotropy="iso__", kinematic="small",
    ))
    seed = pre.rigidDisk(r=0.05, center=[0.0, 0.0], model="rigid", material="BETON")
    ctrl.add(seed)
    ctrl.add(pre.rigidJonc(axe1=0.25, axe2=0.04, center=[1.0, 0.0], model="rigid", material="BETON"))
    ctrl.add(pre.smoothWall(l=2.0, h=0.1, center=[0.0, -0.2], model="rigid", material="BETON"))

    gens = ctrl.apply_for_loop(ForLoop(
        var_name="i", start=0, stop=4, step=1,
        model_avatar_id=seed.avatar_id,
        expr_x="i * 0.2", expr_y="0.3",
        group_name="fline",
    ))
    assert len(gens) == 4
    assert "fline" in ctrl.project.avatar_groups

    law = pre.tact_behav(name="ds1", law="IQS_DS_CLB", dyfr=0.25, stfr=0.35)
    ctrl.add_law(law)
    assert ctrl.project.laws[0].properties == {"dyfr": 0.25, "stfr": 0.35}
    assert ctrl.project.materials[0].properties["young"] == 30e9
