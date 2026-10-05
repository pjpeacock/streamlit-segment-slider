# streamlit-segment-slider

A multi-handle range slider for Streamlit. Drag any number of dividing points along a range to
split it into that many segments -- 2 dividing points make 3 segments (a Cash/Growth/Income-style
split), 3 points make 4, and so on for any count. Pairs with a pie chart + legend by default, or
with per-segment name + percentage labels positioned directly on the track itself, for a much more
compact embed (e.g. one per row in a repeating list).

Built on [Streamlit Custom Components v2](https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component)
and [noUiSlider](https://refreshless.com/nouislider/) (loaded from a CDN at runtime -- see
**Requirements** below). Pure Python, inline component -- no npm install, no build step.

[GitHub repository](https://github.com/pjpeacock/streamlit-segment-slider)

## Install

```bash
pip install streamlit-segment-slider
```

## Usage

```python
import streamlit as st
from streamlit_segment_slider import segment_slider

cuts = segment_slider(
    "Roughly how is it split?",
    min_value=0,
    max_value=100,
    values=[25, 75],
    segment_labels=["Cash", "Growth", "Income"],
    key="my_split",
)

cash_pct = cuts[0]
growth_pct = cuts[1] - cuts[0]
income_pct = 100 - cuts[1]
```

Run `example.py` in this repo for a live demo of both display modes:

```bash
streamlit run example.py
```

## API

```python
segment_slider(
    label,
    min_value,
    max_value,
    values,
    *,
    step=1,
    segment_labels=None,
    key=None,
    show_chart=True,
    show_segment_labels=False,
    height=None,
) -> list[float]
```

| Parameter | Description |
|---|---|
| `label` | Caption shown above the track. Pass `""` to hide that row entirely (not just render it empty) -- useful in compact mode, where the segment labels already say what the slider is for. |
| `min_value`, `max_value` | The full range of the track. |
| `values` | The current dividing points (N values -> N+1 segments). Only used as the seed value the first time this widget's `key` is ever rendered -- after that, Streamlit's own session state owns the live value, same as `value=`/`default=` on any other widget. |
| `step` | Granularity of each handle's movement. |
| `segment_labels` | Exactly N+1 names, one per segment left to right. Left as `None` for generic "Segment 1".."Segment N+1" labels. |
| `key` | Required to track state the normal Streamlit way if you use more than one slider on a page. |
| `show_chart` | Set `False` to drop the pie chart + legend entirely. |
| `show_segment_labels` | Set `True` to label each segment's own name + percentage directly on the track (replaces the plain min/max row). A segment too narrow for its name falls back to just its percentage; one too narrow for either is left blank. Meant to be paired with `show_chart=False` for a compact embed, though either can be toggled independently. |
| `height` | Component height in pixels. Left as `None`, it resolves automatically based on `show_chart`/`label` (390px with the chart shown, ~110-140px without) -- override for anything in between. |

Returns the current list of N dividing values, always sorted ascending (noUiSlider itself keeps
handles from crossing).

## Requirements

- Streamlit >= 1.61.1 (verified against this version; `st.components.v2` is a newer API, so older
  releases won't have it).
- A network path to `cdn.jsdelivr.net` at runtime -- noUiSlider's JS/CSS load from there (pinned
  to `15.8.1`, not `latest`), not from a bundled/vendored copy. If your deployment blocks that CDN,
  this component won't render.

## Limitations

Tested directly (not just inferred) up to 30 segments on one slider -- it never errors, but a few
things degrade past a point:

- **Colors repeat after 10 segments.** The default Streamlit theme exposes exactly 10 categorical
  colors; segment 11 reuses segment 1's color, 12 reuses 2's, and so on. Two differently-named
  segments can end up visually identical once you're past 10.
- **Track labels (`show_segment_labels=True`) need room.** A segment narrower than ~8% of the
  range shows no label at all; one narrower than ~18% shows just its percentage, not its name.
  With many segments (or a few very small ones), most labels go blank -- the handle tooltips above
  the track still show the exact cut points either way.
- **The legend scrolls, not grows, once content is taller than it.** `show_chart=True`'s legend is
  capped at 200px with its own scrollbar for exactly this reason -- without it, a long legend used
  to silently get clipped by the component's fixed `height`, with no scrollbar and no visible sign
  anything was cut off. If you expect many segments, either keep `show_chart=False` (the compact
  label mode doesn't have this problem) or expect your users to scroll the legend.
- **Numeric ranges only** -- `min_value`/`max_value`/`values` are all cast to `float`. Unlike
  native `st.slider`, there's no date/time/datetime support.
- **Shadow DOM isolation.** This component renders with `isolate_styles=True` (the CCv2 default),
  so it's in a shadow root: app-level CSS injected via `st.markdown(unsafe_allow_html=True)` won't
  reach its internals, and a plain `document.querySelector` (including from most browser
  automation/testing tools) won't find them either -- use a tool that pierces shadow roots
  (e.g. Playwright's own locators do this automatically).
- **`st.session_state[key]` is a dict, not a plain list.** Components v2 stores a mounted
  component's state as `{"value": [...]}` under its `key`. Use `segment_slider()`'s own return
  value (always a plain `list[float]`) rather than reading `st.session_state[key]` directly, unless
  you specifically want that wrapper shape.

## License

MIT -- see [LICENSE](LICENSE).
