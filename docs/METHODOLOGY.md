# Valuation conventions and remaining limitations

Valuation date: 9 September 2026. All financial and share amounts in millions. Data are sourced from company reports and issuer-authored regulatory announcements published before the cutoff. Market prices use the unadjusted daily close, not dividend-adjusted prices; raw responses and retrieval timestamps are saved. The model runs offline from the saved snapshot.

## What this analysis answers

What relative share-price range results when Lufthansa's consolidated LTM revenue or adjusted EBITDA is valued at observed European airline trading multiples? This is a comparable-company exercise relevant to M&A work, not a transaction valuation, intrinsic target price or investment recommendation. No control premium, buyer synergies or forecast EBITDA are assumed.

## Peer choice

Air France-KLM and IAG are the closest available network-carrier reference group. They are still imperfect peers: Lufthansa has material MRO and logistics operations; the groups differ in route networks, fleet ownership, labour costs and loyalty businesses. Only two core peers are available. Show both individual multiples and the observed min-max; their midpoint is descriptive, not a statistically robust fair value.

easyJet, Ryanair and Wizz Air form a broader sensitivity set. Different fleet, lease, growth and business mixes make their multiples less directly transferable. easyJet's offer-related news before the valuation date may affect its share price; do not treat its multiple as unaffected standalone trading. Low-cost multiples are a comparison scenario, not an automatically justified premium for Lufthansa.

## LTM and definitions

`data/ltm_bridges.csv` shows source reports, locations and arithmetic. Company-reported rolling EBITDA is used where available. EBITDA definitions remain management-specific: Lufthansa Adjusted, AF-KLM Adjusted, IAG before exceptional items, easyJet Headline, Ryanair reported EBIT plus depreciation, Wizz Air company-reported EBITDA. These have not been completely restated to one uniform accounting definition. A separate Ryanair EUR85m exceptional-charge add-back sensitivity is provided.

Two disclosed differences must remain visible:

- AF-KLM's FY2025 revenue is originally reported, while the H1 comparative was restated for IFRS18. The resulting EUR34,155m LTM bridge is approximate until the FY comparative basis is reconciled. The old model's EUR34,149m is not retained without evidence. EV/Revenue is secondary; this does not change directly reported rolling EBITDA.
- Wizz Air's FY-minus-prior-quarter-plus-current-quarter calculation gives EUR1,165.5m, while the Q1 release explicitly discloses rolling EBITDA of EUR1,164.2m (p12). Use the latter and flag the EUR1.3m difference rather than inventing a reconciliation.

easyJet's LTM and net cash are deliberately measured at 31 March 2026. A newer June trading update existed before the cutoff. Retaining H1 gives a traceable set of full-period metrics but means this peer is lagged; it is not represented as the latest available observation. Excluding easyJet is included in the leave-one-out analysis.

## Currency policy

GBP amounts, including easyJet financials, are translated at the same valuation-date GBP/EUR spot rate. Pence quotes are divided by100 before conversion. This is a constant-currency valuation presentation, not financial-statement consolidation. Translating price, debt and EBITDA consistently preserves native-currency multiples and avoids introducing a purely mechanical difference through mismatched historical-average and spot FX. No claim of economic FX adjustment is made.

## Enterprise value bridge

Baseline EV = basic equity value + lease-inclusive net debt. Debt bridges are in `data/net_debt_bridges.csv`. Negative net debt increases implied equity value. Never add lease liabilities a second time where company net debt already includes them. Ryanair's baseline is rebuilt from disclosed debt, lease liabilities, cash and term deposits; restricted cash is excluded.

The baseline is deliberately labelled **reported-net-debt baseline**, not fully adjusted EV. It omits material non-common-equity claims. An expanded book-proxy sensitivity illustrates:

- Lufthansa: EUR1,585m net pension obligations plus EUR65m minority interests (H1 PDF pp14 and33). Its hybrid is already in financial debt; no duplicate addition or credit-rating 50% equity treatment is used.
- AF-KLM: EUR1,268m parent perpetual capital plus EUR2,136m NCI (H1 PDF p20). NCI includes EUR2,094m perpetuals: do not add those again. June balances do not reflect all July redemptions. Book values are not fair values.
- IAG: EUR6m NCI (H1 PDF p22). Pension assets are not automatically treated as spendable cash.

These are illustrative adjustments, not a fully harmonized bridge. Peer pensions, non-operating investments, restricted funds, hybrids and post-balance-sheet cash flows need additional diligence before calling the output transaction-ready. The model uses the same expanded target bridge when converting enterprise value back into common equity, so adjustments are not applied only to peers.

## Equity and shares

IAG issued shares are reduced by its disclosed treasury shares. Share counts use the latest located disclosure before the cutoff, not a falsely precise exact-day count. Lufthansa and easyJet issued-share disclosures are older; AF-KLM issued shares are a proxy because exact treasury holdings were not reconciled. These limitations are listed in `data/companies.csv`. Voting rights are not substituted for economic shares. Wizz Air uses basic shares with its convertible debt left in debt; using fully diluted shares would require the corresponding debt adjustment and a conversion decision.

## Interpretation

Peer quartiles describe observed cross-sectional dispersion and are not confidence intervals. Two-peer groups show min-max. Leave-one-out results reveal dependence on peer selection. EBITDA/multiple sensitivity is hypothetical, not a forecast. Management EBITDA can exclude recurring economic costs and airlines are capital-intensive; EBITDA alone does not measure distributable cash flow. A conclusion should weigh fleet capex, margins, leverage and earnings sustainability, not average every output into one target price.
