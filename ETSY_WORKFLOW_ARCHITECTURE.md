# Endorphin Etsy Workflow Architecture

Status: current behavior and agreed direction as of 2026-09-25. This document
describes the project context workflow in Endorphin Workshop. The legacy Etsy
Listing nodes remain available for older ComfyUI workflows.

## Project identity and folders

The default root is `G:\My Drive\_Etsy\_Listing`. The Project Selector also
accepts another absolute project root. Artwork and Redesign are separate:

```text
<root>/
├─ artwork/<YYMMNNN>/
│  ├─ artwork_<ID>_transparent.png
│  ├─ base_<ID>_transparent.png
│  ├─ mockup_<ID>_print.png
│  ├─ mockup_<ID>_emb.png
│  └─ emb/mockup_<ID>_emb_<COLOR_CODE>.png
└─ redesign/<RDYYMMNNN>/
   ├─ source/<original reference filename>
   ├─ project.json
   ├─ candidate_<ID>A.png
   └─ <ID>A/mockup_<ID>A_emb_<COLOR_CODE>.png
```

The filenames above show the usual single image outputs. A stage that saves
multiple images in one execution adds `_01`, `_02`, and so on before `.png`.
Artwork may also have `artwork_<ID>.png` as its source. The Redesign `source/`
folder keeps supplier filenames unchanged.

Artwork IDs use `YYMMNNN`; Redesign batch IDs use `RDYYMMNNN`. A Redesign
candidate letter is part of its permanent product ID after approval:
`candidate_RD2608001B.png` belongs to `RD2608001B`. Approval never renumbers
candidate letters.

The Project Selector's Year and Month choose a `YYMM` period. The existing ID
dropdown shows only folders with that period and the selected workflow prefix.
Changing the period clears the current ID. `+ New` uses the same period and
creates the lowest unused ID. Refresh rescans the folder list.

## Artwork stages

| Route | Input resolved from disk | Stage Save output |
| --- | --- | --- |
| `artwork_foundation` | `artwork_<ID>_transparent`, falling back to `artwork_<ID>` | `base_<ID>_transparent.png` |
| `artwork_mockup` with **Print** | `base_<ID>_transparent` | `mockup_<ID>_print.png` |
| `artwork_mockup` with **Embroidery** | `base_<ID>_transparent` | `mockup_<ID>_emb.png` |
| `artwork_stitchwork` | `mockup_<ID>_print`, falling back to old `base_<ID>_print` | `mockup_<ID>_emb.png` |
| `artwork_colorway` | `mockup_<ID>_emb`, falling back to old `base_<ID>_emb` | `emb/mockup_<ID>_emb_<COLOR_CODE>.png` |

Foundation produces the transparent base. Mockup is an AI placement route: it
places that base on a garment mockup and offers Print or Embroidery output.
Stitchwork converts a saved print mockup to an embroidery mockup. Colorway starts
from the embroidery mockup. Missing input files produce an error naming the
expected asset.

Mockup–Embroidery and Stitchwork both write `mockup_<ID>_emb.png`. Today Stage
Save replaces an existing file at that path. Their preview shows whichever
version is currently on disk; the filename does not record which route made it.
Choose the intended producer in the workflow before running either stage.

The selector previews each route's required input and, where available, its
saved output. Mockup's output preview follows the Print/Embroidery choice.
Preview responses bypass browser cache so a replaced file is shown promptly.

## Redesign stages and approval

| Route | Input | Stage Save output |
| --- | --- | --- |
| `redesign_emb_candidate` | First filename sorted image in `source/` | `candidate_<ID><LETTER>.png` |
| `redesign_print_candidate` | First filename sorted image in `source/` | `candidate_<ID><LETTER>.png` |
| `redesign_colorway` | Selected approved candidate image on disk | `<ID><LETTER>/mockup_<ID><LETTER>_emb_<COLOR_CODE>.png` |

Print and embroidery references are two candidate generation routes, not two
sequential stages. Print reference simplification belongs in its AI branch.
The source directory accepts the supported image formats, including AVIF.
Sorting compares filenames without their extensions first, so a base filename
precedes a suffixed variant.

Candidate Save allocates the first unoccupied, unapproved letter, starting with
`A`. It reserves the letter while saving; an IMAGE batch allocates one letter
per image. An unapproved candidate can be deleted and its letter reused.
Approval records the letter in `project.json`; its product ID remains fixed.
Colorway requires an explicitly selected, approved candidate that still exists
on disk. Deleting a candidate through the selector also deletes that
candidate's product folder and its colorways after confirmation.

`project.json` stores the Redesign project ID, source type, approved letters,
and schema version. Actual images on disk remain the source of asset existence.

## Fixed garment color catalogue

The Project Selector palette, standalone Etsy Color Palette, and general Color
Palette Picker use the same 17 rows in this order:

| Index | Color | Code | Index | Color | Code |
| ---: | --- | --- | ---: | --- | --- |
| 1 | Military Green | MGR | 10 | Orange | ORG |
| 2 | Carolina Blue | CBL | 11 | Light Blue | LBL |
| 3 | Navy | NVY | 12 | Forest Green | FGR |
| 4 | Black | BLK | 13 | Beige | BEI |
| 5 | Sand | SND | 14 | Maroon | MRN |
| 6 | Grey | GRY | 15 | Light Pink | LPK |
| 7 | White | WHT | 16 | Brown | BRN |
| 8 | Sport Grey | SGR | 17 | Chocolate | CHC |
| 9 | Ash | ASH |  |  |  |

Names, order, integer values, and three letter codes are fixed. HEX swatches
can be edited directly or with HSL controls; the bundled HEX values are
starting approximations, not verified supplier specifications. A HEX edit does
not change a color's name or code. Clicking a swatch selects its row without
resizing the node. The general Palette Picker also supports a connected
`index_value` that overrides the UI selection at execution time, plus optional
auto increment and loop.

The selected color's name, HEX, and code are included in Etsy context on
Colorway routes. The default prompt text is `<Color Name> (hex #RRGGBB)`.
Stage Save uses the code from context for the output filename; garment type and
size are outside this image pipeline. The full selling SKU is assembled
downstream.

Old garment color suffixes were renamed in the listing asset tree:

| Old | New | Old | New | Old | New |
| --- | --- | --- | --- | --- | --- |
| BLC | BLK | BRW | BRN | TML | BEI |
| DBL | CBL | CHR | GRY | HGR | SGR |
| CRM | MRN | SAG | MGR | FRS | FGR |
| BLS | LPK | SBL | LBL |  |  |

The 2026-09 migration renamed 172 matching files under the default listing
root. This was a one time filesystem rename; the nodes do not translate old
suffixes dynamically. Existing `SND`, `NVY`, `WHT`, and `CHC` filenames
already matched the new catalogue.

## Routing and execution

`ENDORPHIN_ETSY_CONTEXT` carries project root, workflow type, project ID,
selected route, and route specific metadata such as candidate/product ID,
color code, and Mockup Print/Embroidery choice. Image tensors travel through
IMAGE links. The Project Selector emits context and the selected stage's disk
input image.

The Stage Router has one optional lazy IMAGE input per route. It requests only
the selected input from context and forwards that image and context to Stage
Save. Connect the selected stage's generated image to its matching router
input. A missing active connection raises an error; inactive route inputs may
remain unconnected.

Some third party generators are themselves ComfyUI output nodes and may run
even if the lazy router never requests their branch. Put a Stage Branch Gate
before each such generator, with `stage_route` set to that branch. Inactive
gates return an execution blocker. Stage Save reads the route and color from
context, so no separate stage or color code input is needed.

```text
Project Selector context ──────────────┬──────────────> Stage Router context
                                       └──────────────> Stage Save context
Project Selector stage_input_image ──> active AI branch
active AI branch image ────────────────> matching lazy router input
Stage Router image ────────────────────> Stage Save images
```

## Next development directions

These items describe directions discussed for this workflow. They are not
implemented unless explicitly marked above.

1. Make concurrent ownership of `mockup_<ID>_emb.png` explicit. Mockup with
   Embroidery selected and Stitchwork currently share that path. A future
   overwrite policy or provenance marker should prevent accidental replacement
   while keeping the agreed filename.
2. Add an existing asset policy to Stage Save where useful: replace, fail, or
   skip. Current noncandidate saves replace matching paths; candidate saves
   allocate a free letter instead.
3. Keep the Project Selector as the source of project, route, approval, and
   color decisions. New Etsy nodes should consume context and resolve assets
   from disk rather than copying IDs, color lists, or paths into more widgets.
4. Preserve lazy routing as new AI stages are added. Check third party output
   nodes with a Stage Branch Gate so selecting one route never runs unrelated
   generation branches.
5. Keep preview lookup tied to the selected route and saved asset name. When a
   stage replaces an image, its preview should reflect the current disk file.

## Compatibility

Legacy Etsy Listing nodes and generic folder loaders remain available for old
workflows. Artwork input resolution accepts historical `base_<ID>_print` and
`base_<ID>_emb` assets where noted above. Existing workflows that store a
shorter custom palette are normalized to the fixed 17 row catalogue when
loaded; HEX values from a full 17 row palette are retained.
