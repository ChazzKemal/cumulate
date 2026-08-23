# Assumptions

- The tool will use the `Shipments` sheet in `messy.xlsx`.
- The first `Qty` column, containing `120` for `ORD-001`, is the authoritative quantity.
- `Real Quantity` means `Cost` multiplied by the authoritative `Qty` value.
- The negative quantity remains negative in the calculated result.
- Fully duplicate shipment rows remain present and are calculated separately.
- Rows without an Order ID, such as the final totals row, are excluded from shipment calculations.
