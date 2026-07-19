# Inventory Risk Report

## Highest Risk Items
```
                                                SeriesKey                          Product        Country ProductCategory  HorizonDays  InventoryRiskScore  InventoryHealthScore  StockoutRiskScore  OverstockRiskScore  DemandSpikeRiskScore  SupplierDelayRiskScore  InventoryAgeRiskScore  HighRiskDays  MinCoverageDays  MaxUnmetDemandUnits  PotentialRevenueLoss InventoryRiskLevel
PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other PACK OF 72 RETRO SPOT CAKE CASES United Kingdom           Other           30           83.203497             34.722970          82.303008               100.0                 100.0                   100.0                  100.0            30        46.334969                  0.0                   0.0           Critical
PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other PACK OF 72 RETRO SPOT CAKE CASES United Kingdom           Other           60           83.203497             17.361485          82.303008               100.0                 100.0                   100.0                  100.0            60        46.334969                  0.0                   0.0           Critical
PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other PACK OF 72 RETRO SPOT CAKE CASES United Kingdom           Other           90           83.203497             11.574323          82.303008               100.0                 100.0                   100.0                  100.0            90        46.334969                  0.0                   0.0           Critical
PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other PACK OF 72 RETRO SPOT CAKE CASES United Kingdom           Other          180           83.203497              5.787162          82.303008               100.0                 100.0                   100.0                  100.0           180        46.334969                  0.0                   0.0           Critical
PACK OF 72 RETRO SPOT CAKE CASES | United Kingdom | Other PACK OF 72 RETRO SPOT CAKE CASES United Kingdom           Other          365           83.203497              2.853943          82.303008               100.0                 100.0                   100.0                  100.0           365        46.334969                  0.0                   0.0           Critical
       BROCADE RING PURSE  | United Kingdom | Accessories              BROCADE RING PURSE  United Kingdom     Accessories           30           65.000000             95.897890          43.364823               100.0                 100.0                   100.0                  100.0             3        25.532808                  0.0                   0.0               High
       BROCADE RING PURSE  | United Kingdom | Accessories              BROCADE RING PURSE  United Kingdom     Accessories           60           65.000000             82.884647          43.364823               100.0                 100.0                   100.0                  100.0            33        25.532808                  0.0                   0.0               High
       BROCADE RING PURSE  | United Kingdom | Accessories              BROCADE RING PURSE  United Kingdom     Accessories           90           65.000000             80.586198          43.364823               100.0                 100.0                   100.0                  100.0            63        25.532808                  0.0                   0.0               High
       BROCADE RING PURSE  | United Kingdom | Accessories              BROCADE RING PURSE  United Kingdom     Accessories          180           65.000000             79.802094          60.568867               100.0                 100.0                   100.0                  100.0           125        17.776717                  0.0                   0.0               High
       BROCADE RING PURSE  | United Kingdom | Accessories              BROCADE RING PURSE  United Kingdom     Accessories          365           65.000000             77.339770          75.919126               100.0                 100.0                   100.0                  100.0           278        10.856368                  0.0                   0.0               High
```

## Risk Model Comparison
```
         model_name      status                    reason  accuracy  precision   recall       f1  roc_auc     confusion_matrix
      Decision Tree   evaluated                            1.000000   1.000000 1.000000 1.000000      1.0 [[489, 0], [0, 418]]
Logistic Regression   evaluated                            0.998897   0.997613 1.000000 0.998805      1.0 [[488, 1], [0, 418]]
      Random Forest   evaluated                            0.998897   1.000000 0.997608 0.998802      1.0 [[489, 0], [1, 417]]
            XGBoost unavailable  xgboost is not installed       NaN        NaN      NaN      NaN      NaN                   []
           LightGBM unavailable lightgbm is not installed       NaN        NaN      NaN      NaN      NaN                   []
           CatBoost unavailable catboost is not installed       NaN        NaN      NaN      NaN      NaN                   []
```

## Risk Interpretation
- Stockout risk rises when projected stock falls below reorder point and coverage drops under supplier lead time.
- Overstock risk increases when inventory coverage materially exceeds the demand window.
- Demand spike risk reflects widening gaps between base forecast and upper confidence interval.
- Supplier delay risk captures long and volatile replenishment lanes.
- Inventory age risk highlights slow-moving or dead-stock behavior.
