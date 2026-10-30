# Corrected standalone Revision 3 review draft

The review draft is a new deliverable, independent of numerical-release status.
The public current copy is
`reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf`.
`reports/rev3_review/current.json` identifies its immutable edition and PDF hash.
The historical 15-page Revision 2 and its complete provenance are unchanged.

The initial edition uses the actually completed corrected 647657-tetrahedron
field, its actual 216-domain/88-leg mesh, three completed cold mesh levels and
the separately completed 675496-tetrahedron bath case. The geometry is a
source-traced VIGO two-ear, nine Ø0.76 mm C-pin housing plus an independent
TEC Microsystems reference, with assumed internal geometry. It is not an
identified OEM assembly. The report prominently retains failed qualification.
New normal-volume study meshes are identified as pending at this edition's
data freeze; an initial guess is never presented as a solved field.

## Rebuild and inspection

Use the unchanged pinned `fem/run.sh` image for scientific Python and installed
host pdflatex/MuPDF. No package installation, CAD approximation, mesh regeneration
or new solver run is performed by the report builder.

```
python3 reports/rev3_review/build.py --out reports/rev3_review/editions/NEW_EDITION
```

Choose a new edition path. The builder verifies compressed field checksums,
mesh/execution agreement, bijective node positions and tetrahedron connectivity,
then creates exact cut sections, raw owner-flux maps, high-resolution PNG and
PDF figures. All geometry is the corrected actual mesh. The reader sees actual
P1 source-cell means where specified, not smoothed/recovered fields. Signed
bath maps retain negative triangles instead of hiding them with a log scale.

The LaTeX build runs three passes with fixed `SOURCE_DATE_EPOCH`. Validation
checks reader text and decoded metadata, required failures and source dimensions,
page count, text bounds, overflow, figure/input hashes and every rendered page.
Inspect `renders/contact-sheet.png` and dense pages at full size. Record the
actual candidate PDF digest and inspection in `visual_review.json`, then:

```
python3 reports/rev3_review/build.py --publish --out reports/rev3_review/editions/NEW_EDITION
```

Publication requires recorded visual inspection. It snapshots exact report
generators and seals every edition artifact; updating the public current copy
never changes a published edition. CI tests check the current PDF against the
edition ledger, actual corrected archived inputs and generator snapshots.
Hashes and machine paths remain in this external provenance, outside PDF pages.

Run `./fem/run.sh env TE_FEM_SMOKE=1 pytest -q`, existing quick CLI and geometry
demo, and `./fem/run.sh python fem/archive_cold20.py --verify` to check regressions
and preservation. The report validation and reproduction do not qualify the
failed raw 5% cold-interface or 1% bath criteria. See
`docs/REPORT_REVISION3_REVIEW_CRITERIA.md` for unchanged release gates.

## Published editions at this checkpoint

Edition20261030_a retains the initial13-page draft; edition20261030_b adds the
three actual normal-volume studies in a15-page draft. Both have immutable
source/figure/PDF ledgers. The public alias points to b. Cold4.795% passes only
on its own mesh; both new bath levels fail1%, with nonmonotone final error.
The supplement never implies a combined solve or numerical release.

Current generators reject writing into any sealed edition. Calling the current
validator on a sealed edition verifies its ledger without rewriting validation
or render artifacts. The exact generator snapshots remain with each edition;
protective guards added later do not replace those original snapshots.
A standalone three-pass PDF replay of edition a reproduced the identical bytes.
