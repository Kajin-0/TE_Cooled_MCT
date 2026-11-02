# Candidate connector design review — proposal, not qualified geometry

Observed 2026-11-02 UTC; baseline `7d7e9be162a334ee252c4214e7751f903c99b562`.
**STOP:** the user rejects the existing candidate's long Cu posts/ribbons as
unsupported construction. **PENDING:** topology selection and fabrication evidence.
This review changes documentation only: no new CAD, mesh, electrical/thermal
solve, material calibration or runtime recovery. The separate 29/11/4 candidate
is not an identified manufacturer assembly; the original 28/12/4 reference is
unchanged. VIGO housing and independent cooler sources remain unrelated candidates.

## Decision and evidence

Recommend **patterned, electrically isolated face tracks with localized compliant
foil bridges where a real interstage gap must be crossed (A+B)**. Keep metal close
to ceramic terraces and take the shortest *clearance-qualified* route, with a
dedicated peripheral return to the hot side. Use an edge wrap only between
opposite faces of the same ceramic. Do not replace a long post with an equally
long unsupported thin-film column. This is a proposed architecture, **not user
selection, a completed layout or demonstrated manufacturability**. Exact landing
positions, cross sections, corner support and thermal destinations remain open.

Public sources were retrieved locally and inspected, including all three gallery
images below. [Retrieval metadata](../data/tec_connector_proposal_20261102/source_retrieval.json)
records UTC times, URLs, HTTP outcomes and raw-byte hashes; successful reviewed
HTML/images are preserved as lossless gzip snapshots there. Justia returned
403 locally; the same numbered patent was inspected through Google Patents.

| Primary source | Evidence used | What it does not establish |
| --- | --- | --- |
| [TEC Microsystems introduction](https://www.tec-microsystems.com/faq/thermoelectic-coolers-intro.html), conductor/ceramic sections | Miniature conductors generally use deposited Cu-containing multilayers; larger high-power units can use Cu tabs. Ceramics provide electrical insulation and thermal coupling | MC04 film thickness, edge coverage, allowable current density or actual internal netlist |
| [3MC06 family](https://www.tec-microsystems.com/products/thermoelectric-coolers/3mc06-series-thermoelectric-coolers.html), [construction image](https://www.tec-microsystems.com/products/thermoelectric-coolers/images/3mc06-series-thermoelectric-coolers/13_Three-stage_TEC_Construction.jpeg) | Cutaway labels stage connections and metallization junctions near the ceramic stack | A dimensioned connector, process stack or MC04-specific circuit; do not measure dimensions from an illustration |
| Same page: [assembly image](https://www.tec-microsystems.com/products/thermoelectric-coolers/images/3mc06-series-thermoelectric-coolers/Assembly_Technology_Regular_MC06.jpeg), [terminal options](https://www.tec-microsystems.com/products/thermoelectric-coolers/images/3mc06-series-thermoelectric-coolers/17_Three-stage_TEC_Terminal_Connections.jpeg) | Surface assembly and several external termination forms are illustrated, including hot-side pads | Generic external vertical-rod options do **not** substantiate our long internal posts; nor does this source prohibit every rod/tab construction |
| [US4687879A, published 1987-08-18](https://patents.google.com/patent/US4687879A/en), description of Figs.1–4, claims6/7 | Isolated face pads connected by edge metallization or plated apertures; deposition/etch and other patterning methods described | Commercial MC04 construction, present supplier process capability or a directly interchangeable 29/11/4 layout |

The patent's Fig.1 uses special unpaired end P/N blocks and two interstage
connections. It is architectural evidence, not proof that a single edge wrap can
replace our present stage-end links. Its description gives isolated-pattern
spacing of 3–10 mil (76.2–254 µm), typically 127 µm: a historical example,
**not a fabrication rule for this candidate**. It does not specify a qualified
short compliant-foil connector; compliance and dimensions in B are hypotheses.

## Exact circuit constraints and why a cosmetic swap fails

Source pointers: unchanged [geometry author](../tecooledmct/tec_candidate_geometry.py),
[frozen design](../data/tec_candidate_29114_20261101/geometry/design.json),
[prior candidate record](SOURCE_CONSTRAINED_TEC_CANDIDATE_20261101.md).
The series chain is `node0 — legs0…57 — node58 — legs58…79 — node80 —
legs80…87 — node88`: **58/22/8 legs = 29/11/4 couples, 88 legs total**.
Each stage starts N and ends P; the defined forward current travels hot-to-cold
in N and cold-to-hot in P. All its present entry/exit pads are on hot faces.
Retain 44 N,44 P, all **176 full 0.4×0.4 mm axial leg/solder/pad contacts**, and
one unbranched chain, with just two external hot-side terminals. The 89 conductor
nets must stay mutually insulated; new auxiliary lands/joints may change the
solid count, not the circuit or number of P/N contacts. No conductive ceramic.

| Net | Required connection, using frozen leg IDs | Existing Cu-plane z, mm | Existing route length, mm |
| --- | --- | --- | ---: |
| 0 | Hot terminal A to N0 hot pad | 0.515 | 5.60 |
| 58 | P57 hot exit to N58 hot entry | 0.515 → 1.615 | 15.80 |
| 80 | P79 hot exit to N80 hot entry | 1.615 → 2.715 | 12.70 |
| 88 | P87 hot exit to hot terminal B | 2.715 → 0.515 | 9.24 |

Lengths are read-only sums of the frozen route coordinates, excluding added
stubs/tails; [source readout](../data/tec_connector_proposal_20261102/frozen_routing_readout.json).
They are not proposed lengths or electrical predictions. Old hot terminal
centers are `(±2.8,−2.8)` mm; keep two accessible hot-side terminations, with
final landing placement subject to selection/clearance checks. The candidate's
200 µm-diameter short tails do not establish an actual pin1/9 connection or
qualified lead installation. Header pin mapping remains a separate integration gate.

The shared interstage ceramics occupy z=1.10–1.60 and 2.20–2.70 mm. Their
opposite Cu faces are centered at 1.085/1.615 and 2.185/2.715 mm. Thus a wrap
around one 0.5 mm ceramic does **not** connect the hot-to-hot endpoints 1.1 mm
apart in nets58/80, or complete net88's 2.2 mm return. A single fully alternating
even-leg stage has both terminal ends on the same face. Moving an endpoint to
the cold face is a circuit redesign requiring a full polarity/netlist proof,
not a pad-label change. The recommendation preserves these hot-end connections;
it still needs local physical bridges and an explicit return, not hidden jumps.

Alumina bulk separates circuits on its two faces. Patterned tracks on either
face are separate conductors until a **named** wrap/via/tab joins them; a metal
blanket would short multiple nodes. A return track attached to an intermediate
ceramic must remain electrically isolated from nets58/80 while its thermal
contact with that ceramic is explicitly modeled. Segmented return lands cannot
silently become new electrical terminals or connect different nodes.

## Alternatives and their unresolved fabrication constraints

| Option | Proposed use and advantage | Required evidence / limiting issue | Disposition |
| --- | --- | --- | --- |
| A — narrow patterned face/periphery metal, small edge wrap | Ordinary P/N junctions, short face traces and opposite-face ceramic transitions; supported pattern rather than free-standing pillar | Supplier-qualified adhesion/barrier/Cu/finish stack, thickness/resistivity, corner coverage, registration, insulation and solder-compatible edge lands; alone cannot cross present open stage gaps | Preferred face-routing architecture; incomplete as a standalone replacement |
| B — short formed foil/tab bridge | Local adjacent-terrace connections and necessary return hops; limited compliance may relieve differential expansion | Independent foil process/assembly evidence, width/thickness/bend radius, solder lap/fillet, alignment, fatigue and electrical/thermal ratings. No long up-and-over ribbon; actual gap and assembly access must set length | Proposed companion to A; manufacturability PENDING, no qualified heat partition |
| C — plated ceramic via | Opposite-face connection within a ceramic where a supported via process is available | Fabricator evidence for substrate drilling, diameter/annulus/barrel coverage, adhesion/CTE, dielectric clearance and resistance; does not span open interstage gap or eliminate return | Defer; patent shows concept, not current process qualification |

Do not assign a film/foil thickness or an allowable J from appearance, bulk Cu
conductivity or a different family rating. Width, layer thickness, tolerances,
bend radius and allowed current are **UNKNOWN** until source/process evidence
is obtained. The existing 0.1×0.03 mm ribbons and 0.1×0.1 mm pillars are old
assumptions, not manufacturing specifications. Neither the manufacturer pictures
nor the patent establish a safe 1 A rating for any proposed connector.

## Envelope and quantitative qualification requirements — not yet executed

Fixed candidate design constraints remain 6.4 mm bottom /2.4 mm top and 3.8 mm
TEC height, source-informed 0.4×0.4×0.5 mm legs and 29/11/4 allocation; their
source/assumption distinctions remain in the prior candidate record. The old
four 0.5 mm ceramics use 2.0 mm, legs use 1.5 mm, leaving **0.3 mm total** for
six metal/solder layer groups. A proposed film, barrier, solder and any auxiliary
lands must close that budget with tolerances; film thinning cannot silently
alter plate separation. Intermediate plate widths5.2/3.8 mm,0.58 mm pitch,
0.44 mm pad width and0.02 mm solder remain candidate assumptions. Old minimum
pullback0.11 mm and unrelated Cu gap0.14 mm are geometric results, not process rules.

Keep proposed metal/joints inside a checked package clearance envelope at every
terrace, with positive separations from neighboring nets, legs, detector/bonds,
pins, cap and window. Re-evaluate clearances from actual source geometry, not
the old route's PASS flag. The prior cap inner radius7.1 mm and roof9.65 mm
are registered internal assumptions; VIGO external-source alignment does not
identify an OEM assembly. No proposed clearances or revised stack have passed CAD.

For a simple branch of length l, area A and known material law, SI quantities are

`R = ∫ rho(s)/A(s) ds` [ohm], `P_J = I²R` [W],
`J_avg = I/A` [A/m²], `G_th = (∫ ds/[k(s) A(s)])⁻¹` [W/K].

For a uniform constant-property branch, `R*G_th=rho*k`: decreasing electrical
resistance by increasing section or shortening the path increases its passive
thermal conductance. Thin metal can instead raise R/J and corner crowding.
These are design relations, **not calculated candidate performance**. Real
films/foils, contacts, corners and nonisothermal multilayer routing require their
own properties and electrical/thermal operator. Face tracks bonded to several
ceramics form nonlocal heat paths; use actual destinations, not a fitted local
shunt. Require `P=IV=∫J·E dV`, current-cut conservation and polarity reversal;
derive thermal/Joule partition or retain conservative bounds, never a half-split.

The old **0.296705873 ohm** direction-aware centerline estimate and older
0.314364540 ohm estimate belong only to the rejected long-route geometry.
Neither is measured/3D-qualified R or transferable to A/B/C. The old 1 A average
ribbon J≈3.33e8 A/m² is not an allowable current density. No updated Cu R, J
hotspot, Joule power, stage leak or detector temperature has been computed here.

## Gated next action and preserved work

1. **Pending selection:** obtain an actual dimensioned multilayer/edge-metallization
   process example and a compatible foil-joint capability (or documented via
   process for C). Request SI thickness/width/gap/registration tolerances,
   resistivity versus temperature, solder/barrier system and current/fatigue test
   conditions. No supplier contact is sent by this task.
2. **Only after selection and new authorization:** prepare a separately versioned
   netlist/layout with every176 P/N contact owned once, correct cooling polarity,
   89 insulated nets, two hot terminals, real support/joint locations and explicit
   return. Gate stack tolerances, pad footprints, overlaps/clearances, assembly
   access, SI STEP reimport and cap/pin fit before accepting any new CAD.
3. **Only after geometry/process gates and exact runtime verification:** preregister
   a new bounded Stage A electrical/thermal fixture on the selected geometry.
   Reuse independent analytic controls if inspected, not old post-specific cuts,
   port mappings, meshes or qualification claims. B calibration and C sink work
   remain NOT RUN and conditional on qualified conductors/heat partition.

The unchanged [earlier gated draft](GATED_CANDIDATE_CU_20261102.md) contains a
now-suspended resume command. **Do not execute it**, even if the exact missing
image returns. Its preregistration, code snapshots, runtime STOP, source audit
and results remain historical/uncommitted evidence; the user correction changes
future scope, not their bytes. [Pre-change identities](../data/tec_connector_proposal_20261102/preservation_before.json)
cover all existing drafts plus candidate source/STEP and the canonical master.
The current [contract](../AGENTS.md) and append-only [chronology](ENGINEERING_CHRONOLOGY.md)
supersede that obsolete recovery instruction.

Rev3 remains unchanged: a source/design proposal is not qualified new device
science. Original bath1%/cold5%, native gas32.6274% and nonlocal side-port7.277%
failures remain intact. The runtime blocker still prevents required full
regression/semantic archive/legacy checks; **no commit, push or new CI**. Final
documentation, link, preservation and master checks are recorded separately in
[verification.json](../data/tec_connector_proposal_20261102/verification.json).
