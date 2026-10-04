"""A multi-handle range slider for Streamlit.

N draggable dividing points along [min_value, max_value] produce N+1 connected segments --
2 dividing values -> 3 segments (e.g. a Cash/Growth/Income split), 3 dividing values -> 4
segments, and so on for any N. Pairs with either a pie chart + legend (the default) or, for a
more compact embed, per-segment name + percentage labels positioned directly on the track itself
with the chart hidden -- see segment_slider()'s own docstring for both display options.

    from streamlit_segment_slider import segment_slider

    cuts = segment_slider(
        "Roughly how is it split?",
        min_value=0, max_value=100, values=[25, 75],
        segment_labels=["Cash", "Growth", "Income"],
        key="my_split",
    )

See example.py (in this project's root, not this package) for a runnable demo of both display
modes.
"""

import streamlit as st

__all__ = ["segment_slider"]

HTML = """
<link
    rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/nouislider@15.8.1/dist/nouislider.min.css"
/>
<div class="segment-widget">
    <div class="slider-section">
        <div class="slider-label"></div>
        <div class="slider-wrap">
            <div class="multi-slider"></div>
            <div class="segment-labels"></div>
            <div class="range-labels">
                <span class="min-label"></span>
                <span class="max-label"></span>
            </div>
        </div>
    </div>
    <div class="chart-section">
        <div class="pie"></div>
        <div class="legend"></div>
    </div>
</div>
"""

CSS = """
.segment-widget {
    width: 100%;
    font-family: var(--st-font);
    color: var(--st-text-color);
}


/* ---------------------------------------------------------
   SLIDER
--------------------------------------------------------- */

.slider-section {
    width: 100%;
}

.slider-label {
    font-size: 0.875rem;
    font-weight: 400;
    margin-bottom: 0.4rem;
}

.slider-wrap {
    padding: 1.8rem 0.5rem 0;
}


/* Slider track */
.multi-slider.noUi-target {
    height: 6px;
    border: none;
    box-shadow: none;
    background: var(--st-secondary-background-color);
    border-radius: 999px;
}


/* Connections between handles */
.multi-slider .noUi-connect {
    box-shadow: none;
}


/* Slider handles */
.multi-slider .noUi-handle {
    width: 16px;
    height: 16px;
    right: -8px;
    top: -5px;
    border-radius: 50%;
    background: var(--st-background-color);
    border: 2px solid var(--st-primary-color);
    box-shadow: none;
    cursor: grab;
}

.multi-slider .noUi-handle:active {
    cursor: grabbing;
}


/* Remove noUiSlider's default handle lines */
.multi-slider .noUi-handle::before,
.multi-slider .noUi-handle::after {
    display: none;
}


/* Streamlit-like focus */
.multi-slider .noUi-handle:focus {
    outline: none;
    box-shadow:
        0 0 0 3px color-mix(
            in srgb,
            var(--st-primary-color) 25%,
            transparent
        );
}


/* Tooltip */
.multi-slider .noUi-tooltip {
    font-family: var(--st-font);
    font-size: 0.75rem;
    color: var(--st-text-color);
    background: var(--st-background-color);
    border: 1px solid var(--st-border-color);
    border-radius: var(--st-base-radius);
    padding: 0.15rem 0.4rem;
    box-shadow: none;
    bottom: 160%;
}


/* Min/max labels */
.range-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 0.55rem;
    color: var(--st-gray-text-color);
    font-size: 0.75rem;
}


/* Per-segment name + percentage labels -- an alternative to .range-labels above (JS toggles
   which one is visible; only one of the two is ever shown at once), each positioned/sized via
   inline left/width set in JS to match that segment's own span of the track exactly. Hidden
   (empty textContent) by JS for any segment too narrow to hold readable text -- see the JS's
   own comment on those thresholds. */
.segment-labels {
    position: relative;
    height: 1rem;
    margin-top: 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
}

.segment-labels .segment-label {
    position: absolute;
    top: 0;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
}


/* ---------------------------------------------------------
   PIE CHART
--------------------------------------------------------- */
.chart-section {
    margin-top: 2rem;
    display: grid;
    grid-template-columns:
        minmax(150px, 210px)
        minmax(180px, 1fr);
    align-items: center;
    gap: 2rem;
}


/* CSS pie chart */
.pie {
    width: min(100%, 200px);
    aspect-ratio: 1 / 1;
    border-radius: 50%;
    justify-self: center;
    transition: background 60ms linear;
}

/* ---------------------------------------------------------
   LEGEND
--------------------------------------------------------- */
.legend {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
}

.legend-row {
    display: grid;
    grid-template-columns: 12px 1fr auto;
    align-items: center;
    gap: 0.65rem;
    font-size: 0.875rem;
}

.legend-color {
    width: 12px;
    height: 12px;
    border-radius: 3px;
}

.legend-name {
    color: var(--st-text-color);
}

.legend-value {
    color: var(--st-gray-text-color);
    font-variant-numeric: tabular-nums;
}


/* ---------------------------------------------------------
   RESPONSIVE
--------------------------------------------------------- */
@media (max-width: 600px) {
    .chart-section {
        grid-template-columns: 1fr;
    }
    .pie {
        width: 180px;
    }
}
"""


JS = """
import noUiSlider from
    "https://cdn.jsdelivr.net/npm/nouislider@15.8.1/dist/nouislider.min.mjs";

export default function(component) {
    const {
        parentElement,
        data,
        setStateValue
    } = component;


    const slider =
        parentElement.querySelector(".multi-slider");
    const label =
        parentElement.querySelector(".slider-label");
    const segmentLabels =
        parentElement.querySelector(".segment-labels");
    const rangeLabels =
        parentElement.querySelector(".range-labels");
    const minLabel =
        parentElement.querySelector(".min-label");
    const maxLabel =
        parentElement.querySelector(".max-label");
    const chartSection =
        parentElement.querySelector(".chart-section");
    const pie =
        parentElement.querySelector(".pie");
    const legend =
        parentElement.querySelector(".legend");

    /* -----------------------------------------------------
       DISPLAY OPTIONS -- two independent toggles (see
       segment_slider()'s own docstring). Only one of
       segmentLabels/rangeLabels is ever shown at once.
    ----------------------------------------------------- */
    chartSection.style.display =
        data.show_chart ? "grid" : "none";
    segmentLabels.style.display =
        data.show_segment_labels ? "block" : "none";
    rangeLabels.style.display =
        data.show_segment_labels ? "none" : "flex";

    /* -----------------------------------------------------
       SEGMENT COUNT -- driven entirely by how many dividing
       values were passed in (N values -> N+1 segments), not
       a fixed constant. A fresh handle count only matters on
       slider creation below; re-renders just re-derive this
       from whatever data.values currently holds.
    ----------------------------------------------------- */
    const numSegments =
        data.values.length + 1;

    /* -----------------------------------------------------
       TEXT -- an empty/falsy label hides its own element
       entirely (not just empty text), so a caller that
       doesn't want a caption above the track (e.g. one
       embedding this compactly, where the segment labels
       already say what the slider's for) doesn't pay for
       that row's reserved height either.
    ----------------------------------------------------- */
    label.textContent = data.label;
    label.style.display = data.label ? "block" : "none";
    minLabel.textContent = data.min;
    maxLabel.textContent = data.max;

    /* -----------------------------------------------------
       GET STREAMLIT CHART COLORS
    ----------------------------------------------------- */
    const widget =
        parentElement.querySelector(".segment-widget");
    const styles =
        getComputedStyle(widget);

    function cssVar(name, fallback) {
        const value =
            styles.getPropertyValue(name).trim();
        return value || fallback;
    }

    let palette = [];
    const categorical =
        styles
            .getPropertyValue("--st-chart-categorical-colors")
            .trim();

    if (categorical) {
        palette =
            categorical
                .split(",")
                .map(c =>
                    c
                        .trim()
                        .replace(/^["']|["']$/g, "")
                );
    }

    /* Fallback to Streamlit semantic colors if the theme didn't expose a categorical palette */
    if (palette.length === 0) {
        palette = [
            cssVar("--st-blue-color", "#0068c9"),
            cssVar("--st-orange-color", "#ff8700"),
            cssVar("--st-green-color", "#09ab3b"),
            cssVar("--st-violet-color", "#803df5"),
            cssVar("--st-red-color", "#ff2b2b")
        ];
    }

    /* One color per segment -- cycles (modulo) if there are more segments than colors in the
       palette, a graceful fallback for an unusually high segment count rather than a hard error;
       realistic uses (budget splits, allocations) are expected to stay well under the palette
       size. */
    const colors =
        Array.from(
            { length: numSegments },
            (_, i) => palette[i % palette.length]
        );

    /* -----------------------------------------------------
       NUMBER FORMAT
    ----------------------------------------------------- */
    const decimals =
        data.decimals ?? 0;
    function formatValue(value) {
        return Number(value)
            .toFixed(decimals);
    }

    /* -----------------------------------------------------
       DRAW PIE + LEGEND
    ----------------------------------------------------- */
    function render(values) {
        values =
            values
                .map(Number)
                .sort((a, b) => a - b);

        const total =
            data.max - data.min;

        /* N dividing values -> N+1 segment widths, via consecutive differences across
           [min, ...values, max]. */
        const boundaryPoints = [
            data.min,
            ...values,
            data.max
        ];
        const segmentValues = [];
        for (let i = 0; i < boundaryPoints.length - 1; i++) {
            segmentValues.push(
                boundaryPoints[i + 1] - boundaryPoints[i]
            );
        }

        const percentages =
            segmentValues.map(
                value => value / total * 100
            );

        /* Cumulative percentage boundaries for the conic-gradient stops (0 .. 100), built as a
           running sum. */
        const boundaries = [0];
        percentages.forEach(
            p => boundaries.push(
                boundaries[boundaries.length - 1] + p
            )
        );

        /* Pie + legend -- skipped entirely when show_chart is off, same data this function
           always computes either way (boundaries/percentages feed the segment labels below too). */
        if (data.show_chart) {
            /* Pie -- stop list built dynamically (one "<color> <start>% <end>%" term per segment). */
            const stops =
                colors
                    .map(
                        (color, i) =>
                            `${color} ${boundaries[i]}% ${boundaries[i + 1]}%`
                    )
                    .join(",\\n");
            pie.style.background =
                `conic-gradient(${stops})`;

            /* Legend */
            legend.replaceChildren();
            segmentValues.forEach(
                (value, index) => {
                    const row =
                        document.createElement("div");
                    row.className =
                        "legend-row";
                    const swatch =
                        document.createElement("span");
                    swatch.className =
                        "legend-color";
                    swatch.style.background =
                        colors[index];
                    const name =
                        document.createElement("span");
                    name.className =
                        "legend-name";
                    name.textContent =
                        data.segment_labels[index];
                    const amount =
                        document.createElement("span");
                    amount.className =
                        "legend-value";
                    amount.textContent =
                        `${formatValue(value)}  (${percentages[index].toFixed(1)}%)`;
                    row.append(
                        swatch,
                        name,
                        amount
                    );

                    legend.appendChild(row);
                }
            );
        }

        /* Per-segment name + percentage labels -- the compact alternative to the chart. Each
           label sits directly over its own segment's span of the track (left/width set to the
           same boundaries the pie's conic-gradient stops use), so it stays aligned with the
           colored region below even while dragging. Three width tiers (not one all-or-nothing
           cutoff) since the segment's own name (data.segment_labels[index], e.g. "Growth") is
           usually longer than just its percentage and needs more room to read without
           overlapping its neighbors: wide enough for both (>= 18%) shows "Name NN%"; too narrow
           for the name but not the number (>= 8%) shows just "NN%"; anything narrower than that
           is left blank entirely -- the legend (when shown) or the handle tooltips still carry
           the exact numbers either way. */
        if (data.show_segment_labels) {
            segmentLabels.replaceChildren();
            percentages.forEach(
                (pct, index) => {
                    const span =
                        document.createElement("span");
                    span.className =
                        "segment-label";
                    span.style.left =
                        `${boundaries[index]}%`;
                    span.style.width =
                        `${pct}%`;
                    span.style.color =
                        colors[index];
                    const pctText =
                        `${pct.toFixed(0)}%`;
                    span.textContent =
                        pct >= 18
                            ? `${data.segment_labels[index]} ${pctText}`
                            : pct >= 8
                                ? pctText
                                : "";
                    segmentLabels.appendChild(span);
                }
            );
        }
    }

    /*
       Store the newest render function on the slider.
       That matters because Streamlit can rerun this JavaScript
       after Python state changes without recreating the slider.
    */
    slider._streamlitRender = render;

    /* -----------------------------------------------------
       CREATE SLIDER ONCE
    ----------------------------------------------------- */
    if (!slider.noUiSlider) {
        noUiSlider.create(
            slider,
            {
                start: data.values,
                step: data.step,
                range: {
                    min: data.min,
                    max: data.max
                },
                /*
                   N handles create N+1 connected regions --
                   one "true" per segment, not a fixed entry count.
                */
                connect: Array(numSegments).fill(true),
                behaviour: "tap",
                tooltips: {
                    to: value =>
                        formatValue(value),
                    from: value =>
                        Number(value)
                }
            }
        );

        /* Color the N slider regions */
        const connections =
            slider.querySelectorAll(
                ".noUi-connect"
            );

        connections.forEach(
            (connection, index) => {
                connection.style.background =
                    colors[index];
            }
        );


        /*
           UPDATE fires continuously while dragging.
           Only redraw the chart here.
           No Streamlit rerun.
        */

        slider.noUiSlider.on(
            "update",
            (
                values,
                handle,
                unencoded
            ) => {

                slider._streamlitRender(
                    unencoded
                );
            }
        );

        /*
           CHANGE fires when the user releases the handle.

           NOW send the values back to Python.
        */
        slider.noUiSlider.on(
            "change",
            (
                values,
                handle,
                unencoded
            ) => {
                setStateValue(
                    "value",
                    unencoded.map(
                        value =>
                            Number(
                                value.toFixed(decimals)
                            )
                    )
                );
            }
        );
    }

    /* -----------------------------------------------------
       SYNC FROM PYTHON
    ----------------------------------------------------- */
    else {
        const current =
            slider.noUiSlider
                .get(true)
                .map(Number);
        const incoming =
            data.values.map(Number);
        const changed =
            incoming.some(
                (value, index) =>
                    Math.abs(
                        value - current[index]
                    ) > 1e-9
            );
        if (changed) {
            slider.noUiSlider.set(
                incoming
            );
        }

        render(incoming);
    }
}
"""

_segment_slider_component = st.components.v2.component(
    name="segment_slider",
    html=HTML,
    css=CSS,
    js=JS,
)


def _decimal_places(step):
    text = f"{step:.10f}".rstrip("0")
    if "." not in text:
        return 0
    return len(text.split(".")[1])


def segment_slider(
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
):
    """A slider with a variable number of draggable dividing points along [min_value, max_value],
    paired with a pie chart + legend -- N dividing values (`values`) produce N+1 connected
    segments (e.g. 2 values -> 3 segments, a Cash/Growth/Income-style split; 3 values -> 4
    segments). `segment_labels`, if given, must have exactly N+1 entries (one per segment, left
    to right); left as None to get generic "Segment 1..N+1" labels.

    `show_chart=False` drops the pie + legend section entirely -- useful when embedding this
    compactly, e.g. once per row in a repeating list, where the full pie+legend design reads as
    too much space per instance. `show_segment_labels=True` replaces the plain min/max row under
    the track with each segment's own name + percentage (e.g. "Growth 80%"), color-matched and
    positioned directly over that segment's own span of the track -- meant as a compact substitute
    for the legend when the chart is hidden, though either option can be toggled independently of
    the other. A segment too narrow to fit its name falls back to just its percentage, and one too
    narrow for either is left blank rather than overlapping its neighbors.

    `height` is exposed (not hardcoded) so a caller can size this to its own layout; left as None,
    it resolves to 390px with the chart shown, or ~75-100px with the chart hidden (less again if
    `label` is also left empty, since that row then takes no space at all) -- override it
    explicitly for anything in between.

    Returns the current list of N dividing values (floats, always sorted ascending -- noUiSlider
    itself keeps handles from crossing, so this never needs to re-sort or re-validate what comes
    back).
    """
    num_points = len(values)
    if num_points < 1:
        raise ValueError(
            "segment_slider requires at least one dividing value (so at least two segments)."
        )
    num_segments = num_points + 1

    if segment_labels is None:
        segment_labels = [f"Segment {i + 1}" for i in range(num_segments)]
    if len(segment_labels) != num_segments:
        raise ValueError(
            f"segment_labels must contain exactly {num_segments} label(s) for {num_points} "
            f"dividing value(s) ({num_points} value(s) -> {num_segments} segments)."
        )

    default_values = list(map(float, values))

    # A keyed Components v2 component stores its state as a dictionary in Session State.
    state = st.session_state.get(key, {})
    if isinstance(state, dict):
        current_values = state.get("value", default_values)
    else:
        current_values = default_values

    if height is None:
        # Each branch measured, not guessed, against the rendered widget's own bounding box, plus
        # a small safety margin -- a too-generous default here leaves a visible gap of dead space
        # before whatever comes after this widget on the page. 390 (chart shown) is the original
        # design height, unaffected by label. Chart hidden: ~88px measured with a label shown,
        # ~59px with label="" (the label row itself hides entirely when empty) -- these aren't the
        # same height, so this resolves on both show_chart and whether label is actually set.
        if show_chart:
            height = 390
        elif label:
            height = 100
        else:
            height = 75

    result = _segment_slider_component(
        data={
            "label": label,
            "min": float(min_value),
            "max": float(max_value),
            "values": current_values,
            "step": float(step),
            "decimals": _decimal_places(step),
            "segment_labels": list(segment_labels),
            "show_chart": bool(show_chart),
            "show_segment_labels": bool(show_segment_labels),
        },
        default={"value": default_values},
        on_value_change=lambda: None,
        key=key,
        width="stretch",
        height=height,
    )

    return list(result.value)
