from lmgc90_core import Material, MaterialType
from lmgc90_engine.materialize import _make_material


class PreStub:
    def __init__(self):
        self.kwargs = None

    def material(self, **kwargs):
        self.kwargs = kwargs
        return kwargs


def _materialize(material_type, properties, density=1000.0):
    pre = PreStub()
    material = Material(
        name="MAT01",
        material_type=MaterialType(material_type),
        density=density,
        properties=properties,
    )
    _make_material(pre, material)
    return pre.kwargs


def test_elas_dila_drops_unsupported_orthotropic_fields_and_keeps_dilatation():
    kwargs = _materialize("ELAS_DILA", {
        "elas": "standard",
        "anisotropy": "orthotropic",
        "young": 3e10,
        "nu": 0.2,
        "G12": 1e10,
        "alpha": 1.2e-5,
        "T_ref_meca": 20.0,
    })

    assert kwargs["anisotropy"] == "isotropic"
    assert kwargs["dilatation"] == 1.2e-5
    assert kwargs["T_ref_meca"] == 20.0
    assert "G" not in kwargs
    assert "G12" not in kwargs


def test_visco_elas_uses_pylmgc_viscous_options_and_drops_legacy_names():
    kwargs = _materialize("VISCO_ELAS", {
        "elas": "standard",
        "anisotropy": "orthotropic",
        "young": 1.17e11,
        "nu": 0.35,
        "viscosity": 1e6,
        "viscous_model": "KelvinVoigt",
        "viscous_young": 1.17e9,
        "viscous_nu": 0.35,
        "G12": 1e10,
    })

    assert kwargs["anisotropy"] == "isotropic"
    assert kwargs["viscous_model"] == "KelvinVoigt"
    assert kwargs["viscous_young"] == 1.17e9
    assert kwargs["viscous_nu"] == 0.35
    assert "viscosity" not in kwargs
    assert "G" not in kwargs


def test_elas_plas_legacy_names_are_mapped_to_supported_options():
    kwargs = _materialize("ELAS_PLAS", {
        "sigc": 2.5e8,
        "hard": 1e9,
        "critere": "Von-Mises",
        "isoh": "linear",
        "cinh": "none",
        "visc": "none",
    })

    assert kwargs["iso_hard"] == 2.5e8
    assert kwargs["isoh_coeff"] == 1e9
    assert "sigc" not in kwargs
    assert "hard" not in kwargs


def test_thermo_and_poro_legacy_aliases_map_to_supported_names():
    thermo = _materialize("THERMO_ELAS", {
        "alpha": 1e-5,
        "capacity": 500.0,
        "conductivity": 2.0,
    })
    poro = _materialize("PORO_ELAS", {
        "biot": 0.8,
        "permeability": 1e-8,
        "capacity": 1e-10,
    })

    assert thermo["dilatation"] == 1e-5
    assert thermo["specific_capacity"] == 500.0
    assert "capacity" not in thermo
    assert poro["hydro_cpl"] == 0.8
    assert poro["conductivity"] == 1e-8
    assert poro["specific_capacity"] == 1e-10
    assert "biot" not in poro
    assert "permeability" not in poro


def test_discrete_vectors_are_converted_for_pylmgc():
    kwargs = _materialize("DISCRETE", {
        "masses": "1, 2",
        "stiffnesses": "100, 200",
        "viscosities": "0, 0",
    })

    assert kwargs["masses"] == [1.0, 2.0]
    assert kwargs["stiffnesses"] == [100.0, 200.0]
    assert kwargs["viscosities"] == [0.0, 0.0]
    assert "density" not in kwargs


def test_external_material_does_not_receive_unsupported_density():
    kwargs = _materialize("EXTERNAL", {})

    assert "density" not in kwargs