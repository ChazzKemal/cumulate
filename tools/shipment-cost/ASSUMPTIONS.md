# Assumptions

- The `Cost` value is the total cost for that shipment row, not a per-unit price.
- Total cost means adding the `Cost` values from the shipment rows; quantity is displayed for context but is not multiplied by cost.
- The final mostly blank row is an existing totals row and must be excluded from the calculation to avoid counting the total twice.
- The shipment Cost values are the source of truth. Their calculated sum is `5,492.00`; the workbook's existing total of `5,492.25` is shown as a discrepancy rather than substituted for the calculation.
- Both identical `ORD-003` rows are included because the workbook's existing total includes both of them.
- The negative `ORD-002` quantities are valid and remain in the data; its positive cost is included as supplied.
- Both quantity columns should be shown because the workbook contains two columns named `Qty`, and their distinct business meanings are not stated.
