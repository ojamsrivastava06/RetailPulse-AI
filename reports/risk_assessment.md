# RetailPulse Risk Assessment

## Risk Summary

```
      RiskDomain  RiskScore RiskLevel                                                                                Drivers                                                         RecommendedMitigation
   Forecast Risk      23.90       Low                            Demand variance, forecast error, and revenue concentration.    Review high-error series and validate near-term replenishment assumptions.
  Inventory Risk      36.19       Low            Stockout exposure, overstock exposure, coverage days, and reorder pressure. Prioritize P0/P1 replenishment, safety stock, and warehouse transfer actions.
   Customer Risk      42.10       Low       Churn probability, customer health, lifetime value at risk, and engagement drop.              Launch retention actions for high-value critical-risk customers.
    Revenue Risk      32.95       Low          Revenue at risk from demand drop, stockouts, churn, and low product velocity.                    Protect top revenue drivers and rebalance promotion focus.
   Supplier Risk      20.33       Low                  Lead-time pressure, supplier delay risk, and fulfillment constraints.      Escalate supplier lanes tied to critical SKUs and high revenue exposure.
Operational Risk      45.70    Medium Warehouse allocation, fulfillment readiness, action urgency, and execution complexity.                 Assign owners for immediate actions and track weekly closure.
```

## Alert Evidence

```
 AlertID           AlertType Severity      Domain                                                    Entity  PriorityScore RiskLevel                                                              RecommendedAction
AL-00001 Revenue Opportunity     High    Customer                                                 Champions          75.46       Low                Offer premium assortment, bundles, and loyalty-tier incentives.
AL-00002 Revenue Opportunity   Medium    Customer                                                 Champions          61.73       Low                Offer premium assortment, bundles, and loyalty-tier incentives.
AL-00003    Customer Leaving   Medium       Churn                                                     13902          56.09       Low                                                            Send Email Campaign
AL-00004 Revenue Opportunity   Medium    Customer                                                 Champions          54.67       Low                Offer premium assortment, bundles, and loyalty-tier incentives.
AL-00005    Customer Leaving   Medium       Churn                                                     12482          48.77       Low                                                            Send Email Campaign
AL-00006 Revenue Opportunity   Medium    Customer                                                 Champions          48.63       Low                Offer premium assortment, bundles, and loyalty-tier incentives.
AL-00007 Revenue Opportunity   Medium    Customer                                                 Champions          45.81       Low                Offer premium assortment, bundles, and loyalty-tier incentives.
AL-00010      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.31    Medium                                                                Supplier Review
AL-00011      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.31    Medium                                                                  Reorder Today
AL-00012      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.31    Medium                                                     Demand Buffer Optimization
AL-00013      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.30    Medium                                                                  Reorder Today
AL-00014      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.30    Medium                                                                Supplier Review
AL-00015      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.30    Medium                                                     Demand Buffer Optimization
AL-00016      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.29    Medium                                                                Supplier Review
AL-00017      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.29    Medium                                                                  Reorder Today
AL-00018      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.29    Medium                                                     Demand Buffer Optimization
AL-00019      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.28    Medium                                                                Supplier Review
AL-00020      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.28    Medium                                                     Demand Buffer Optimization
AL-00021      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.28    Medium                                                                  Reorder Today
AL-00022      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.28    Medium                                                                  Reorder Today
AL-00023      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.28    Medium                                                                Supplier Review
AL-00024      Supplier Delay   Medium   Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other          44.28    Medium                                                     Demand Buffer Optimization
AL-00080        Demand Spike   Medium Forecasting                                            Global Revenue          40.41    Medium Align inventory, pricing, and promotion planning to capture forecasted demand.
AL-00081        Demand Spike   Medium Forecasting                                            United Kingdom          40.41    Medium Align inventory, pricing, and promotion planning to capture forecasted demand.
AL-00082        Demand Spike   Medium Forecasting                                            Global Revenue          40.28    Medium Align inventory, pricing, and promotion planning to capture forecasted demand.
```
