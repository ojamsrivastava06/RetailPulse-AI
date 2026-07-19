# RetailPulse Executive Decision Report

Generated from the completed RetailPulse data engineering, customer intelligence, forecasting, inventory, churn, and Streamlit platform artifacts.

## Executive Summary

```
             SummaryType                               Title    Value                                                                                                                Narrative Priority           Owner  Timeframe          GeneratedAt
       Top Opportunities Upsell Premium Products - Champions  $57,612                                                          Offer premium assortment, bundles, and loyalty-tier incentives.       P1  Executive Team  This Week 2026-07-16 17:21 UTC
               Top Risks Increase Inventory - Global Revenue   Medium                                         Forecasted demand and revenue justify proactive commercial and inventory action.       P3      Risk Owner    Monitor 2026-07-16 17:21 UTC
         Critical Alerts          119 active business alerts        1                                                 Critical and high alerts require weekly executive tracking until closed.    P0/P1      Operations  Immediate 2026-07-16 17:21 UTC
           Business Wins          Projected financial impact $706,938 Decision engine combines revenue opportunity, inventory savings, cost reduction, retention gain, and profit improvement.       P1         Finance This Month 2026-07-16 17:21 UTC
         Revenue Drivers                 Revenue opportunity $277,584                               Primary drivers are demand capture, promotions, bundles, and premium upsell opportunities.       P1      Commercial  This Week 2026-07-16 17:21 UTC
            Loss Drivers              Scenario downside risk     High                                          Capture revenue upside while pre-allocating inventory and fulfillment capacity.       P1        Planning  This Week 2026-07-16 17:21 UTC
       Immediate Actions                 0 immediate actions       $0                           Immediate actions are the highest priority operating decisions for the next executive standup.       P0 Decision Office  Immediate 2026-07-16 17:21 UTC
Weekly Executive Summary                      Holiday Season $206,386                                          Capture revenue upside while pre-allocating inventory and fulfillment capacity.       P1  Executive Team     Weekly 2026-07-16 17:21 UTC
```

## Top Priority Decisions

```
DecisionID PriorityBand  PriorityScore               DecisionType    Domain                                                    Entity  FinancialImpact  ExpectedROI RiskLevel                                                 SuggestedAction
  DI-00001           P1          75.46    Upsell Premium Products  Customer                                                 Champions         57612.12      1043.33       Low Offer premium assortment, bundles, and loyalty-tier incentives.
  DI-00002           P2          61.73    Upsell Premium Products  Customer                                                 Champions         40985.42      1013.37       Low Offer premium assortment, bundles, and loyalty-tier incentives.
  DI-00003           P2          56.09 Retain High Value Customer     Churn                                                     13902         15450.02       579.20       Low                                             Send Email Campaign
  DI-00004           P2          54.67    Upsell Premium Products  Customer                                                 Champions         32430.71       987.34       Low Offer premium assortment, bundles, and loyalty-tier incentives.
  DI-00005           P3          48.77 Retain High Value Customer     Churn                                                     12482         10467.61       511.93       Low                                             Send Email Campaign
  DI-00006           P3          48.63    Upsell Premium Products  Customer                                                 Champions         25100.00       952.85       Low Offer premium assortment, bundles, and loyalty-tier incentives.
  DI-00007           P3          45.81    Upsell Premium Products  Customer                                                 Champions         21688.13       930.17       Low Offer premium assortment, bundles, and loyalty-tier incentives.
  DI-00008           P3          44.75           Reduce Overstock Inventory    ASSORTED COLOUR BIRD ORNAMENT | United Kingdom | Decor          9982.98       565.75       Low                                      Demand Buffer Optimization
  DI-00009           P3          44.53        Supplier Escalation Inventory    ASSORTED COLOUR BIRD ORNAMENT | United Kingdom | Decor          9628.61       454.65       Low                                                 Supplier Review
  DI-00010           P3          44.31        Supplier Escalation Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other           470.51       -54.82    Medium                                                 Supplier Review
  DI-00011           P3          44.31        Supplier Escalation Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other           470.51       -54.82    Medium                                                   Reorder Today
  DI-00012           P3          44.31        Supplier Escalation Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other           470.51       -54.82    Medium                                      Demand Buffer Optimization
  DI-00013           P3          44.30        Supplier Escalation Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other           443.18       -57.34    Medium                                                   Reorder Today
  DI-00014           P3          44.30        Supplier Escalation Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other           443.18       -57.34    Medium                                                 Supplier Review
  DI-00015           P3          44.30        Supplier Escalation Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other           443.18       -57.34    Medium                                      Demand Buffer Optimization
  DI-00016           P3          44.29        Supplier Escalation Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other           429.23       -58.63    Medium                                                 Supplier Review
  DI-00017           P3          44.29        Supplier Escalation Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other           429.23       -58.63    Medium                                                   Reorder Today
  DI-00018           P3          44.29        Supplier Escalation Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other           429.23       -58.63    Medium                                      Demand Buffer Optimization
  DI-00019           P3          44.28        Supplier Escalation Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other           420.66       -59.43    Medium                                                 Supplier Review
  DI-00020           P3          44.28        Supplier Escalation Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other           420.66       -59.43    Medium                                      Demand Buffer Optimization
```

## Critical Alerts

```
 AlertID           AlertType Severity    Domain                                                    Entity                                                                                                           Message                                               RecommendedAction  PriorityScore RiskLevel  FinancialImpact TimeSensitivity DecisionID
AL-00001 Revenue Opportunity     High  Customer                                                 Champions                                             Upsell Premium Products recommended for Champions with priority 75.5. Offer premium assortment, bundles, and loyalty-tier incentives.          75.46       Low         57612.12       This Week   DI-00001
AL-00002 Revenue Opportunity   Medium  Customer                                                 Champions                                             Upsell Premium Products recommended for Champions with priority 61.7. Offer premium assortment, bundles, and loyalty-tier incentives.          61.73       Low         40985.42      This Month   DI-00002
AL-00003    Customer Leaving   Medium     Churn                                                     13902                                              Retain High Value Customer recommended for 13902 with priority 56.1.                                             Send Email Campaign          56.09       Low         15450.02      This Month   DI-00003
AL-00004 Revenue Opportunity   Medium  Customer                                                 Champions                                             Upsell Premium Products recommended for Champions with priority 54.7. Offer premium assortment, bundles, and loyalty-tier incentives.          54.67       Low         32430.71      This Month   DI-00004
AL-00005    Customer Leaving   Medium     Churn                                                     12482                                              Retain High Value Customer recommended for 12482 with priority 48.8.                                             Send Email Campaign          48.77       Low         10467.61         Monitor   DI-00005
AL-00006 Revenue Opportunity   Medium  Customer                                                 Champions                                             Upsell Premium Products recommended for Champions with priority 48.6. Offer premium assortment, bundles, and loyalty-tier incentives.          48.63       Low         25100.00         Monitor   DI-00006
AL-00007 Revenue Opportunity   Medium  Customer                                                 Champions                                             Upsell Premium Products recommended for Champions with priority 45.8. Offer premium assortment, bundles, and loyalty-tier incentives.          45.81       Low         21688.13         Monitor   DI-00007
AL-00010      Supplier Delay   Medium Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other Supplier Escalation recommended for PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other with priority 44.3.                                                 Supplier Review          44.31    Medium           470.51         Monitor   DI-00010
AL-00011      Supplier Delay   Medium Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other Supplier Escalation recommended for PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other with priority 44.3.                                                   Reorder Today          44.31    Medium           470.51         Monitor   DI-00011
AL-00012      Supplier Delay   Medium Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other Supplier Escalation recommended for PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other with priority 44.3.                                      Demand Buffer Optimization          44.31    Medium           470.51         Monitor   DI-00012
AL-00013      Supplier Delay   Medium Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other Supplier Escalation recommended for PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other with priority 44.3.                                                   Reorder Today          44.30    Medium           443.18         Monitor   DI-00013
AL-00014      Supplier Delay   Medium Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other Supplier Escalation recommended for PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other with priority 44.3.                                                 Supplier Review          44.30    Medium           443.18         Monitor   DI-00014
AL-00015      Supplier Delay   Medium Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other Supplier Escalation recommended for PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other with priority 44.3.                                      Demand Buffer Optimization          44.30    Medium           443.18         Monitor   DI-00015
AL-00016      Supplier Delay   Medium Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other Supplier Escalation recommended for PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other with priority 44.3.                                                 Supplier Review          44.29    Medium           429.23         Monitor   DI-00016
AL-00017      Supplier Delay   Medium Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other Supplier Escalation recommended for PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other with priority 44.3.                                                   Reorder Today          44.29    Medium           429.23         Monitor   DI-00017
AL-00018      Supplier Delay   Medium Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other Supplier Escalation recommended for PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other with priority 44.3.                                      Demand Buffer Optimization          44.29    Medium           429.23         Monitor   DI-00018
AL-00019      Supplier Delay   Medium Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other Supplier Escalation recommended for PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other with priority 44.3.                                                 Supplier Review          44.28    Medium           420.66         Monitor   DI-00019
AL-00020      Supplier Delay   Medium Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other Supplier Escalation recommended for PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other with priority 44.3.                                      Demand Buffer Optimization          44.28    Medium           420.66         Monitor   DI-00020
AL-00021      Supplier Delay   Medium Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other Supplier Escalation recommended for PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other with priority 44.3.                                                   Reorder Today          44.28    Medium           420.66         Monitor   DI-00021
AL-00022      Supplier Delay   Medium Inventory PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other Supplier Escalation recommended for PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other with priority 44.3.                                                   Reorder Today          44.28    Medium           407.85         Monitor   DI-00022
```

## Scenario Outlook

```
               Scenario  RevenueImpact  InventoryImpact  ProfitImpact RiskLevel                                                                 RecommendedResponse
            Demand +10%      398668.50          5256.59      68308.31    Medium                 Monitor scenario indicators and keep current operating plan active.
            Demand +20%      797337.00         10513.17     134812.05    Medium                 Monitor scenario indicators and keep current operating plan active.
            Demand -20%     -797337.00         10513.17    -151552.56    Medium         Reduce exposure, preserve cash, and focus promotions on recoverable demand.
         Holiday Season     1218330.94         14718.44     206385.69      High     Capture revenue upside while pre-allocating inventory and fulfillment capacity.
         Supplier Delay     -159467.40          2102.63     -28866.86      High     Escalate critical suppliers, confirm lead times, and protect high-revenue SKUs.
     Inventory Shortage     -398668.50          5256.59    -113381.61    Medium           Prioritize replenishment, safety stock, and warehouse transfer decisions.
Customer Churn Increase     -199334.25          2628.29    -267580.38    Medium   Fund retention actions for high-value customers and monitor weekly risk movement.
         Price Increase       47840.22          4205.27     -51280.20    Medium           Validate price elasticity and protect demand-sensitive customer segments.
         Price Discount      194550.23          7359.22      29464.38    Medium Use margin guardrails and target discounts to slow-moving or bundle-ready products.
```
