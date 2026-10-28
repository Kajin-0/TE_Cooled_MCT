# Parametric CAD reference (separate from physics solver)

Run with the optional **CadQuery** package installed:

    python geometry/reference_cad.py

It generates a two-view STEP assembly in geometry/generated/. The model is a deliberately simplified mechanical starting point. It places 88 semiconductor legs, four ceramic plates, a small detector and NTC thermistor, nine glass-to-metal feedthroughs and a windowed cap, with the TEC dimensions constrained to the published 3MC04-044-05 external envelope.

**Not OEM exact:** tapered flange simplified to an ellipse, stage allocation inferred 28/12/4, pad metallization unverified, electrical circuit unconnected, solder/thermal contacts not calibrated, no detailed bond-wire routing. Treat generated STEP as a **visual geometry reference**, not valid coupled FEM mesh or circuit model. See docs/rev6_cad_audit.md. The full earlier Rev6 visual source and model files are available separately in the packaged project download.
