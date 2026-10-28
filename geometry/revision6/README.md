# Revision 6 visual geometry

The full parametric CAD source and associated STEP/GLB and HTML views were generated in the earlier detector-modeling workflow and are included with the downloadable project archive. The current published GitHub directory documents the dimensions and audit constraints, while Phase 0 uses a separate reduced-order solver independent of the geometry export.

**Do not use the visual STEP directly as multiphysics input:** unintended 15/10/6 µm gaps, incomplete interstage electrical topology, approximate stage placement and contact locations. See docs/rev6_cad_audit.md. For quantitative 3D work, build the simulation-grade geometry from parametric material/contact interfaces with verified electrical netlist.
