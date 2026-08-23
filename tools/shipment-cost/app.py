"""Calculate shipment cost totals from the supplied workbook."""
import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st


import os  # noqa: E402
PROJECT_ROOT = Path(os.environ.get("CUMULATE_APP")
                    or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(PROJECT_ROOT / "scaffold"))
from account import sign_in_panel  # noqa: E402
from feedback import feature_box  # noqa: E402
from mysessions import my_sessions_panel  # noqa: E402
from ingest import load, list_sheets  # noqa: E402


def remove_existing_total_row(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """Remove a final summary row so its cost is not counted twice."""
    if df.empty:
        return df.copy(), False

    last = df.iloc[-1]
    identifying_columns = [
        column
        for column in ("Order ID", "Ship Date", "Carrier")
        if column in df.columns
    ]
    looks_like_total = (
        bool(identifying_columns)
        and last[identifying_columns].isna().all()
        and last.isna().sum() > len(df.columns) / 2
    )
    if looks_like_total:
        return df.iloc[:-1].reset_index(drop=True), True
    return df.reset_index(drop=True), False


def make_download(shipments: pd.DataFrame, total_cost: float) -> bytes:
    output = BytesIO()
    summary = pd.DataFrame({"Measure": ["Total cost"], "Value": [total_cost]})
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, index=False, sheet_name="Summary")
        shipments.to_excel(writer, index=False, sheet_name="Shipments")
    return output.getvalue()


st.set_page_config(page_title="Shipment Cost Total", layout="wide")

sign_in_panel()
st.title("Shipment Cost Total")
st.caption("Read shipment quantities and costs, then calculate the total cost.")

default_file = PROJECT_ROOT / "inbox" / "messy.xlsx"
uploaded = st.file_uploader(
    "Use a different spreadsheet (optional)",
    type=["xlsx", "xls", "csv"],
)

if uploaded:
    temporary_file = PROJECT_ROOT / ".streamlit_upload" / uploaded.name
    temporary_file.parent.mkdir(exist_ok=True)
    temporary_file.write_bytes(uploaded.getbuffer())
    source_file = temporary_file
    source_name = uploaded.name
elif default_file.exists():
    source_file = default_file
    source_name = default_file.name
else:
    st.info("Add a spreadsheet above to calculate its total cost.")
    st.stop()

sheets = list_sheets(source_file) if source_file.suffix.lower() != ".csv" else ["(csv)"]
sheet = st.selectbox("Sheet", sheets) if len(sheets) > 1 else sheets[0]
data = load(source_file, sheet=0 if sheet == "(csv)" else sheet)
shipments, removed_total = remove_existing_total_row(data)
existing_total_cost = None
if removed_total and "Cost" in data.columns:
    parsed_existing_total = pd.to_numeric(
        pd.Series([data.iloc[-1]["Cost"]]), errors="coerce"
    ).iloc[0]
    if pd.notna(parsed_existing_total):
        existing_total_cost = float(parsed_existing_total)

quantity_columns = [column for column in shipments.columns if str(column).startswith("Qty")]
if "Cost" not in shipments.columns:
    st.error("This sheet does not contain a Cost column.")
    st.stop()
if not quantity_columns:
    st.error("This sheet does not contain a quantity column.")
    st.stop()

costs = pd.to_numeric(shipments["Cost"], errors="coerce")
total_cost = float(costs.sum())

st.success(f"Loaded {len(shipments):,} shipment rows from {source_name}")

metrics = st.columns(1 + len(quantity_columns))
metrics[0].metric("Total cost", f"{total_cost:,.2f}")
for metric, column in zip(metrics[1:], quantity_columns):
    quantity_total = pd.to_numeric(shipments[column], errors="coerce").sum()
    metric.metric(f"Total {column}", f"{quantity_total:,.0f}")

if removed_total:
    st.caption("The workbook's existing totals row was excluded from the calculation.")
if (
    existing_total_cost is not None
    and abs(existing_total_cost - total_cost) > 0.005
):
    st.warning(
        f"The workbook's existing total is {existing_total_cost:,.2f}, which differs "
        f"from the shipment cost sum by {existing_total_cost - total_cost:,.2f}."
    )
if len(quantity_columns) > 1:
    st.caption(
        "The source contains two columns named Qty; both are shown using the loader's "
        "distinct labels."
    )

display_columns = [
    column
    for column in ["Order ID", "Ship Date", *quantity_columns, "Cost"]
    if column in shipments.columns
]
result = shipments[display_columns].copy()

st.subheader("Shipment details")
st.dataframe(
    result.style.format({"Cost": "{:,.2f}"}),
    width="stretch",
    hide_index=True,
)

st.download_button(
    "Download results",
    make_download(result, total_cost),
    "shipment_cost_total.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

with st.expander("What this tool assumes"):
    assumptions = Path(__file__).parent / "ASSUMPTIONS.md"
    st.markdown(assumptions.read_text())

my_sessions_panel()
feature_box(Path(__file__).parent.name)
