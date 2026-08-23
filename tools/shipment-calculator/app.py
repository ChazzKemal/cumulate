"""Calculate real quantity from shipment cost and the first quantity column."""
import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scaffold"))
from ingest import load, list_sheets  # noqa: E402


def calculate_real_quantity(data: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Return shipment rows with Cost × the authoritative first Qty column."""
    required = ["Order ID", "Qty", "Cost"]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(
            "The selected sheet is missing: " + ", ".join(missing)
        )

    excluded_rows = int(data["Order ID"].isna().sum())
    result = data.loc[data["Order ID"].notna()].copy().reset_index(drop=True)
    quantity = pd.to_numeric(result["Qty"], errors="coerce")
    cost = pd.to_numeric(result["Cost"], errors="coerce")
    result["Real Quantity"] = cost * quantity
    return result, excluded_rows


def make_download(result: pd.DataFrame) -> bytes:
    """Create a workbook containing the calculated shipment rows and summary."""
    output = BytesIO()
    total = result["Real Quantity"].sum(min_count=1)
    summary = pd.DataFrame(
        {
            "Measure": ["Shipment rows", "Total Real Quantity"],
            "Value": [len(result), total],
        }
    )
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, index=False, sheet_name="Summary")
        result.to_excel(writer, index=False, sheet_name="Shipments")
    return output.getvalue()


st.set_page_config(page_title="Shipment Real Quantity", layout="wide")
st.title("Shipment Real Quantity")
st.caption("Multiply each shipment's cost by the first Qty column.")

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
    st.info("Add a spreadsheet above to calculate real quantity.")
    st.stop()

sheets = list_sheets(source_file) if source_file.suffix.lower() != ".csv" else ["(csv)"]
sheet = st.selectbox("Sheet", sheets) if len(sheets) > 1 else sheets[0]
data = load(source_file, sheet=0 if sheet == "(csv)" else sheet)

try:
    result, excluded_rows = calculate_real_quantity(data)
except ValueError as error:
    st.error(str(error))
    st.stop()

invalid_rows = int(result[["Qty", "Cost"]].isna().any(axis=1).sum())
total_real_quantity = result["Real Quantity"].sum(min_count=1)

st.success(f"Loaded {len(result):,} shipment rows from {source_name}")

metric_rows, metric_total = st.columns(2)
metric_rows.metric("Shipment rows", f"{len(result):,}")
metric_total.metric(
    "Total Real Quantity",
    f"{total_real_quantity:,.2f}" if pd.notna(total_real_quantity) else "—",
)

st.caption("Real Quantity = Cost × Qty (the first Qty column)")

if excluded_rows:
    st.info(
        f"Excluded {excluded_rows:,} row without an Order ID, including the workbook's totals row."
    )
if result.duplicated(subset=[column for column in data.columns]).any():
    duplicate_count = int(
        result.duplicated(subset=[column for column in data.columns]).sum()
    )
    st.warning(f"Kept {duplicate_count:,} fully duplicate shipment row in the calculation.")
if (pd.to_numeric(result["Qty"], errors="coerce") < 0).any():
    st.info("Negative quantities remain negative in the calculated result.")
if invalid_rows:
    st.warning(
        f"{invalid_rows:,} shipment row could not be calculated because Qty or Cost is blank."
    )

display_columns = [
    column
    for column in ["Order ID", "Ship Date", "Qty", "Cost", "Real Quantity"]
    if column in result.columns
]

st.subheader("Calculated shipments")
st.dataframe(
    result[display_columns].style.format(
        {"Qty": "{:,.0f}", "Cost": "{:,.2f}", "Real Quantity": "{:,.2f}"},
        na_rep="—",
    ),
    width="stretch",
    hide_index=True,
)

st.download_button(
    "Download results",
    make_download(result),
    "shipment_real_quantity.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

with st.expander("What this tool assumes"):
    assumptions = Path(__file__).parent / "ASSUMPTIONS.md"
    st.markdown(assumptions.read_text())
