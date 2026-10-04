"""Demo for streamlit_segment_slider -- run with:

    streamlit run example.py

Shows both display modes: the default (a pie chart + legend) and the compact mode (chart
hidden, segment name + percentage labeled directly on the track) meant for embedding this
inline several times in a row, e.g. one per item in a repeating list.
"""

import streamlit as st

from streamlit_segment_slider import segment_slider

st.set_page_config(page_title="segment_slider demo")

st.title("segment_slider")
st.write(
    "A multi-handle range slider: drag any number of dividing points to split "
    "[min_value, max_value] into that many segments."
)

st.header("Default: pie chart + legend")
cuts = segment_slider(
    "Divide the population",
    min_value=0,
    max_value=100,
    values=[25, 50, 75],
    step=1,
    segment_labels=["Group A", "Group B", "Group C", "Group D"],
    key="population_segments",
)
st.write("Dividing points:", cuts)

st.divider()

st.header("Compact mode: no chart, labels on the track")
st.caption("show_chart=False, show_segment_labels=True -- e.g. a Cash/Growth/Income split")
compact_cuts = segment_slider(
    "",
    min_value=0,
    max_value=100,
    values=[25, 75],
    step=1,
    segment_labels=["Cash", "Growth", "Income"],
    key="compact_demo_segments",
    show_chart=False,
    show_segment_labels=True,
)
st.write("Dividing points:", compact_cuts)
