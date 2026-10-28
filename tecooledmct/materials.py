"""Sourced first-pass bulk materials for TEC/TO-66 investigations.

These values are NOT measured for the specific 3MC04-044-05's P/N dopants or
a specific detector package. Each property carries provenance and temperature.
Do not extrapolate 300 K constants to the ~190 K cold junction as fact.
All computations in SI units.
"""
from dataclasses import dataclass
from typing import Optional
import math

@dataclass(frozen=True)
class Material:
    name: str
    thermal_conductivity_w_mk: float
    density_kg_m3: Optional[float]=None
    heat_capacity_j_kgk: Optional[float]=None
    expansion_per_k: Optional[float]=None
    electrical_resistivity_ohm_m: Optional[float]=None
    seebeck_v_k: Optional[float]=None
    temperature_k: float=293.15
    status: str="literature_reference"
    source_url: str=""
    notes: str=""

# For doped TEC legs: S_p=+160 and S_n=-170 uV/K, room-temperature
# conductivity respectively 1400 and 1655 S/cm (from a literature example).
# BiTe k=~1.5 W/m/K is approximate Ferrotec bulk BiTe reference, NOT a
# measurement of these same doped specimens and not OEM grade-specific.
P_BI_TE=Material(
    name="Bi2Te3_based_p_type_literature_example", thermal_conductivity_w_mk=1.5,
    density_kg_m3=7529,heat_capacity_j_kgk=544,expansion_per_k=12.9e-6,
    electrical_resistivity_ohm_m=1/(1400*100),seebeck_v_k=160e-6,
    temperature_k=300.,status="mixed_literature_illustrative",
    source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5453363/",
    notes="S and sigma same published example; k, cp, density from generic Ferrotec BiTe, not same sample.")
N_BI_TE=Material(
    name="Bi2Te3_based_n_type_literature_example", thermal_conductivity_w_mk=1.5,
    density_kg_m3=7529,heat_capacity_j_kgk=544,expansion_per_k=12.9e-6,
    electrical_resistivity_ohm_m=1/(1655*100),seebeck_v_k=-170e-6,
    temperature_k=300.,status="mixed_literature_illustrative",
    source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5453363/",
    notes="S and sigma same published example; k, cp, density from generic Ferrotec BiTe, not same sample.")
ALUMINA_96=Material(
    name="alumina_96_percent_CoorsTek_AD96",thermal_conductivity_w_mk=24.7,
    density_kg_m3=3720,heat_capacity_j_kgk=880,expansion_per_k=8.2e-6,
    temperature_k=293.15,status="vendor_grade_proxy",
    source_url="https://www.coorstek.com/en/materials/alumina/",
    notes="k at 20 C, cp at 100 C, expansion averaged 25-1000 C; not same-temperature data.")
ALUMINA_HIGH_PURITY=Material(
    name="alumina_99_5_percent_CoorsTek_AD995",thermal_conductivity_w_mk=30.,
    density_kg_m3=3900,heat_capacity_j_kgk=880,expansion_per_k=8.2e-6,
    temperature_k=293.15,status="vendor_grade_proxy",
    source_url="https://www.coorstek.com/en/materials/alumina/",
    notes="TEC OEM says 100% Al2O3; 99.5% grade is a PROXY, not that exact material. Cp at 100 C.")
KOVAR=Material(
    name="Kovar_F15_alloy",thermal_conductivity_w_mk=17.3,
    density_kg_m3=8360,heat_capacity_j_kgk=.105*4184,
    expansion_per_k=5.5e-6,temperature_k=293.15,status="vendor_bulk_reference",
    source_url="https://www.ametekinterconnect.com/-/media/ametek-ecp/v2/files/cw_datasheets_sds_cfsi/datasheets/kovar.pdf?la=en",
    notes="Density 8.36 g/cm3; cp 0.105 cal/g/K specified at 0 C; k typical; header Kovar assumption not OEM-verified.")
GOLD_WIRE_4N=Material(
    name="gold_bonding_wire_4N",thermal_conductivity_w_mk=315.,
    density_kg_m3=19340,heat_capacity_j_kgk=129,expansion_per_k=14.1e-6,
    electrical_resistivity_ohm_m=2.3e-8,temperature_k=293.15,
    status="gold_bond_wire_datasheet",
    source_url="https://www.inseto.com/wp-content/uploads/2022/08/Gold-Wire-Data-Sheet.pdf",
    notes="99.99% Au min with trace dopants; not Au-In alloy. Cp from generic 300 K Au reference.")
SN_SB_95_5=Material(
    name="Sn95Sb5_Indalloy133_reference",thermal_conductivity_w_mk=64.7,
    density_kg_m3=7250,expansion_per_k=31e-6,temperature_k=293.15,
    status="alloy_proxy_not_TEC_exact_composition",
    source_url="https://documents.indium.com/qdynamo/download.php?docid=4064",
    notes="TEC maker says Sn-Sb but does NOT disclose exact ratio; 95Sn5Sb is representative alloy only.")
COPPER=Material(
    name="copper_bulk_reference",thermal_conductivity_w_mk=400.,
    density_kg_m3=8960,heat_capacity_j_kgk=385,expansion_per_k=16.7e-6,
    electrical_resistivity_ohm_m=1.72e-8,temperature_k=295.15,
    status="representative_bulk_proxy",
    source_url="https://www.nist.gov/srd",
    notes="High-purity Cu typical at room temperature, not the measured plating/copper alloy.")
MATERIALS={m.name:m for m in (P_BI_TE,N_BI_TE,ALUMINA_96,ALUMINA_HIGH_PURITY,KOVAR,GOLD_WIRE_4N,SN_SB_95_5,COPPER)}

def one_dimensional_resistance(material:Material, length_m:float, area_m2:float,
                               contact_resistance_k_w:float=0.):
    """Thermal resistance K/W of simple uniform planar layer; 1D spreading neglected."""
    if length_m<=0 or area_m2<=0 or contact_resistance_k_w<0:
        raise ValueError("positive dimensions, nonnegative interface resistance required")
    return length_m/(material.thermal_conductivity_w_mk*area_m2)+contact_resistance_k_w

def layer_temperature_drop(material:Material, thickness_mm:float, width_mm:float,
                           heat_load_w:float,contact_resistance_k_w:float=0.):
    """A geometry-based layer estimate, NOT full package FEA or a TEC stage prediction."""
    area=(width_mm*1e-3)**2
    r=one_dimensional_resistance(material,thickness_mm*1e-3,area,contact_resistance_k_w)
    return {"material":material.name,"thermal_resistance_k_w":r,"delta_t_k":heat_load_w*r,
            "heat_load_w":heat_load_w,"assumption":"1-D constant k, no spreading; no Peltier"}
