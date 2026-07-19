# RetailPulse Business KPIs

## KPI Catalog
| Category | KPI | Definition | Primary Measure | Business Use |
| --- | --- | --- | --- | --- |
| Sales | Total Revenue | Total monetized sales captured by the transaction fact | `Total Revenue` | Executive revenue tracking |
| Sales | Total Orders | Unique orders or invoices in context | `Total Orders` | Order volume and demand pace |
| Sales | Average Order Value | Revenue per order | `Average Order Value` | Basket quality and upsell tracking |
| Sales | Revenue Growth % | Current revenue versus prior-year revenue | `Revenue Growth %` | Growth momentum |
| Sales | Gross Profit | Revenue after estimated margin | `Gross Profit` | Profitability analysis |
| Sales | Profit Margin | Gross profit as a percentage of revenue | `Profit Margin` | Margin efficiency |
| Sales | Revenue per Customer | Revenue divided by unique customers | `Revenue per Customer` | Monetization per account |
| Forecast | Forecast Revenue | Total forecasted revenue for the selected horizon | `Forecast Revenue` | Planning and demand review |
| Forecast | Forecast Demand | Total forecasted units or demand for the selected horizon | `Forecast Demand` | Supply planning |
| Forecast | Forecast Accuracy % | Accuracy against actual evaluation rows | `Forecast Accuracy %` | Model quality |
| Forecast | MAPE | Mean absolute percentage error | `MAPE` | Forecast error benchmark |
| Forecast | Forecast Error | Signed residual across evaluation rows | `Forecast Error` | Bias detection |
| Inventory | Inventory Cost | Carrying, stockout, and optimization cost combined | `Inventory Cost` | Cost-to-serve analysis |
| Inventory | Inventory Savings | Cost avoided by optimized stock policy | `Inventory Savings` | Value from optimization |
| Inventory | Inventory Turnover | Average stock turns in context | `Inventory Turnover` | Stock efficiency |
| Inventory | Stock Coverage | Average days of coverage | `Stock Coverage` | Replenishment visibility |
| Inventory | Safety Stock | Average safety buffer units | `Safety Stock` | Reorder planning |
| Inventory | EOQ | Economic order quantity | `EOQ` | Order size guidance |
| Inventory | High Risk Inventory Series | Number of series with high or critical risk | `High Risk Inventory Series` | Exception management |
| Customer | Total Customers | Unique customers in context | `Total Customers` | Customer base size |
| Customer | Average CLV | Average predicted lifetime value | `Average CLV` | Value concentration |
| Customer | Customer Lifetime Value | Portfolio value across customers | `Customer Lifetime Value` | Long-term revenue potential |
| Customer | Average Health Score | Average churn-health score | `Average Health Score` | Retention health |
| Customer | Churn Rate | Share of customers predicted to churn | `Churn Rate` | Retention urgency |
| Customer | Retention Rate | Share of customers expected to remain active | `Retention Rate` | Loyalty strength |
| Customer | High Risk Customers | Customers in critical or high risk states | `High Risk Customers` | Retention workload |
| Customer | VIP Customers | Customers with VIP health band | `VIP Customers` | Priority service list |
| Executive | Dynamic KPI | KPI selected by the user or field parameter | `Dynamic KPI` | Executive flexibility |
| Executive | Variance | Difference between the selected KPI and target | `Variance` | Gap analysis |
| Executive | Target Achievement % | Progress against target | `Target Achievement %` | Goal tracking |
| Executive | Country Revenue | Revenue in the selected geography context | `Country Revenue` | Regional performance |
| Executive | Category Revenue | Revenue in the selected category context | `Category Revenue` | Category contribution |

## KPI Design Notes
- Pair every top-line KPI with a trend measure or a variance measure.
- Use a consistent definition across all pages so cards do not contradict each other.
- If a KPI is target-driven, show both `Variance` and `Target Achievement %` together.
- Keep executive KPIs to a small set of headline metrics and move technical diagnostics to analysis pages.
