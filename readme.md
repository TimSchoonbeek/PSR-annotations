# Procedure Step Recognition (PSR) Annotations and Annotator Tool 

> For the most up-to-date information, visit the [**project page**](https://timschoonbeek.github.io/stormpsr.html)

This repository provides:
- Annotator tools to help you efficiently annotate and convert video sequences into PSR step labels for your own datasets.
- A concise overview of **MECCANO states** (what each part/state index means) and **PSR** (Procedure Step Recognition). These are formatted to mirror [**IndustReal PSR Annotations**](https://timschoonbeek.github.io/industreal.html).
- **ASD** (Assembly State Detection) annotations for MECCANO.

---

## Repository layout

```
.
├── MECCANO_ASD_Annotations/
│   ├── train/
│   ├── val/
│   └── test/
├── MECCANO_PSR_Annotations/
│   ├── train/<recording_id>/{PSR_labels.csv, PSR_labels_raw.csv, PSR_labels_with_errors.csv}
│   ├── val/<recording_id>/...
│   └── test/<recording_id>/...
├── PSR_labeler.py
├── auto_labeling.py
└── Overview of the states in MECCANO.pdf
```

---

## MECCANO states: quick overview

In MECCANO, a **binary/ternary state vector** tracks whether each part is correctly placed:

- **1** = correctly installed  
- **0** = not installed / absent  
- **-1** = incorrectly installed (error state)

The vector indexes map to the parts parts in **“Overview of the states in MECCANO.pdf”**, that summarizes the state coding and example aggregate “state strings”.

---

## Annotations format (aligned with IndustReal)

See the [**IndustReal**](https://timschoonbeek.github.io/industreal.html) page for reference.

### 1) PSR Annotations (per recording)

Located at: `MECCANO_PSR_Annotations/<split>/<recording_id>/`

- **`PSR_labels.csv`**  
  Compact per-frame action list:
  ```
  <image_name>,<step_id>,<step_description>
  ```
  Example:
  ```
  01259.jpg,24,Install headlamp
  02127.jpg,26,Remove headlamp
  ```

- **`PSR_labels_raw.csv`**  
  Full state vector per frame (multi-label):
  ```
  <image_name>,s0,s1,...,s16
  ```
  where `s_k ∈ {-1, 0, 1}` for each of the components.

- **`PSR_labels_with_errors.csv`** *(optional)*  
  Like `PSR_labels.csv` but includes steps arising from error transitions (e.g., “Incorrectly installed …”).  
  Format:
  ```
  <image_name>,<step_id>,<step_description>
  ```

### 2) ASD Annotations (per recording)

Located at: `MECCANO_ASD_Annotations/<split>/`

For each sequence `XXXX_GT.csv`:
```
<frame_idx> <track_id> <class_id> <x_center> <y_center> <width> <height>
```
- Coordinates are **normalized** to `[0, 1]` (YOLO-style).
- `class_id` encodes the action/state class for ASD.
- `track_id` typically denotes the person/actor ID (single or multiple tracks).

This format mirrors the IndustReal ASD exports.

---

## Public tools for building your own PSR datasets

With these two scripts you can annotate your own data easily.

### `PSR_labeler.py` — interactive state labeler

An OpenCV-based tool to **manually label per-frame state vectors** (`-1/0/1` per part). Typical workflow:

1. Organize each recording as a folder with sequential frames (`.jpg`).
2. Set the PSR_labeler.py parameters (load dir, save dir, FPS, but also the components to include in PSR annotations)
3. Run the labeler
4. Use the on-screen UI and keyboard to:
   - Navigate frames (step, skip, rewind).
   - Toggle each part’s state among `-1` (incorrect), `0` (absent), `1` (correct).
5. The tool writes out a `PSR_labels_raw.csv`

> Tip: The script also visualizes current state and provides basic controls (skip/rewind/fast-forward) to speed up labeling.

### `auto_labeling.py` — convert states to PSR step events

This script **converts** `PSR_labels_raw.csv` sequences into action/step annotations (**`PSR_labels.csv`**). It implements the state-transition rules described above and can optionally include error-induced steps.

**Expected `procedure_info.json`**
A minimal example schema:
```json
[
  { "description": "Install left damping fork" },
  { "description": "Incorrectly install left damping fork" },
  { "description": "Remove left damping fork" },

  { "description": "Install right damping fork" },
  { "description": "Incorrectly install right damping fork" },
  { "description": "Remove right damping fork" }

  // ... continue so that index == step_id
]
```
- It should be a **list** where the **index equals `step_id`**.
- Each entry must contain at least a `"description"` field.

**Toggles & options**
- Set `include_errors` in `convert_all_states_to_steps(...)` to `True` if you want `*_with_errors.csv` logic.
- The script currently defaults to scanning **train/val/test**; you can also pass flags in code (`get_recording_list(..., train=True)` etc.) if you want only one split.

## Citation & Acknowledgements

If you use these annotations or tools, please cite the corresponding article:

```bibtex
@misc{schoonbeek2025learning,
  title={Learning to Recognize Correctly Completed Procedure Steps in Egocentric Assembly Videos through Spatio-Temporal Modeling},
  author={Tim J. Schoonbeek and Shao-Hsuan Hung and Dan Lehman and Hans Onvlee and Jacek Kustra and Peter H. N. de With and Fons van der Sommen},
  year={2025},
  eprint={2510.12385},
  archivePrefix={arXiv},
  primaryClass={cs.CV},
  url={https://arxiv.org/abs/2510.12385},
}

