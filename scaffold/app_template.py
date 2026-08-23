"""Starting point for a tool. Replace the marked section; leave the rest alone."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# The shared code may live somewhere else entirely — a tool sits in the person's
# own folder, the scaffold ships with the app and is updated separately.
import os  # noqa: E402
_app = Path(os.environ.get("CUMULATE_APP") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(_app / "scaffold"))
from ingest import load, list_sheets  # noqa: E402
from account import sign_in_panel  # noqa: E402
from feedback import feature_box  # noqa: E402
from mysessions import my_sessions_panel  # noqa: E402

st.set_page_config(page_title="TOOL_NAME", layout="wide")

sign_in_panel()
st.title("TOOL_NAME")
st.caption("ONE_LINE_DESCRIPTION")

uploaded = st.file_uploader("Spreadsheet", type=["xlsx", "xls", "csv"])
if not uploaded:
    st.info("Drop your file above to start.")
    st.stop()

tmp = Path(".streamlit_upload") / uploaded.name
tmp.parent.mkdir(exist_ok=True)
tmp.write_bytes(uploaded.getbuffer())

sheets = list_sheets(tmp) if tmp.suffix != ".csv" else ["(csv)"]
sheet = st.selectbox("Sheet", sheets) if len(sheets) > 1 else sheets[0]
df = load(tmp, sheet=0 if sheet == "(csv)" else sheet)

st.success(f"Loaded {len(df):,} rows × {len(df.columns)} columns")

# ---------------------------------------------------------------- BUILD HERE
result = df
# ---------------------------------------------------------------------------

st.subheader("Result")
st.dataframe(result, use_container_width=True)

col1, col2 = st.columns(2)
col1.metric("Rows in", f"{len(df):,}")
col2.metric("Rows out", f"{len(result):,}")

buf = Path(".streamlit_upload") / "result.xlsx"
with pd.ExcelWriter(buf, engine="openpyxl") as w:
    result.to_excel(w, index=False, sheet_name="Result")
st.download_button("Download as Excel", buf.read_bytes(), "result.xlsx")

with st.expander("What this tool assumes"):
    a = Path(__file__).parent / "ASSUMPTIONS.md"
    st.markdown(a.read_text() if a.exists() else "_No assumptions recorded._")

my_sessions_panel()
feature_box(Path(__file__).parent.name)
