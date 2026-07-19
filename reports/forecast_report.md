# Forecast Report

## Overview
RetailPulse Phase 3.5 upgrades the existing forecasting workflow into a modular enterprise pipeline with advanced lag, rolling, expanding, calendar, and business features. The workflow uses rolling-origin backtesting, TimeSeriesSplit validation, hyperparameter search, recursive feature elimination, explainability outputs, and multi-horizon forecasting.

## Dependency Status
- statsmodels: available
- xgboost: unavailable
- lightgbm: unavailable
- catboost: unavailable
- prophet: unavailable
- pmdarima: unavailable
- tensorflow: unavailable
- shap: unavailable

## Best Model
- Selected model: **Holt-Winters**
- Configuration: **default**
- Rationale: Holt-Winters (default) won because it produced the lowest RMSE (404.39) and improved on the Naive baseline by 12.3%.

## Leaderboard Snapshot
```
           model_name configuration  series_count        mae       rmse        mape      smape          r2      mase  selection_eligible
         Holt-Winters       default             5 195.037128 404.386716 4996.838273 111.035000   -6.428141  2.209167                True
                  MLP       default             5 193.841107 408.279667 5301.282766 120.369011   -7.588638  2.518206                True
                ARIMA       default             5 190.483489 408.425695 5501.740423 119.024702   -4.228452  2.055137                True
Exponential Smoothing       default             5 171.681479 409.102155 4128.616104 117.892903   -3.997407  1.982601                True
               SARIMA       default             5 197.052031 409.412104 5597.012640 120.342533   -9.517294  2.659833                True
           ElasticNet         tuned             5 210.700622 412.668356 5312.507867 128.027713  -15.462613  3.150649                True
                  MLP         tuned             5 204.020855 435.734006 5399.558204 122.692945  -12.620246  2.972732                True
       Moving Average       default             5 294.186545 453.579838 9324.281361 130.363598   -0.773778  1.469888                True
                Naive       default             5 236.391111 460.871042 4516.200385 112.864202   -0.616076  1.009523                True
             AdaBoost       default             5 212.504301 467.484795 6999.422713 119.136306 -609.133524 11.584877                True
           ElasticNet       default             5 272.410812 485.113294 7514.032503 134.837559  -26.492834  4.037280                True
                Ridge       default             5 273.255613 486.038785 7562.844711 134.771619  -26.819220  4.048238                True
```

## Hyperparameter Optimization
```
model_name search_strategy  selected_feature_count  best_rmse                                                                     best_params
  AdaBoost            grid                      20 141.507229                                    {"learning_rate": 0.05, "n_estimators": 100}
       MLP          random                      20 155.259973 {"alpha": 0.0005, "hidden_layer_sizes": [128, 64], "learning_rate_init": 0.005}
ElasticNet            grid                      20 172.681426                                                 {"alpha": 0.1, "l1_ratio": 0.2}
```

## Feature Interpretation
- **Lag_21**: Three-week demand helps identify repeat buying cycles.
- **Lag_7**: Seven-day demand reflects weekly shopping cadence and promotions.
- **Lag_14**: Two-week demand stabilizes recent volatility.
- **ExpandingMean**: Cumulative mean encodes the long-run demand level.
- **RollingStd_14**: Two-week variability captures demand turbulence.
- **RollingMean_14**: Biweekly averages smooth transient noise.
- **WeeklyGrowth**: Weekly growth captures short trend changes.
- **ProductFrequency**: Product frequency shows how persistently the item moves.
- **ProductDemand**: Product-level demand captures cross-market item popularity.
- **RollingStd_30**: Monthly variability helps flag planning risk.

## Explainability Tables
### Feature Importance
```
          feature  importance            source_model
           Lag_21    0.157928 Surrogate Random Forest
            Lag_7    0.073946 Surrogate Random Forest
           Lag_14    0.068250 Surrogate Random Forest
    ExpandingMean    0.047450 Surrogate Random Forest
    RollingStd_14    0.040002 Surrogate Random Forest
   RollingMean_14    0.038494 Surrogate Random Forest
     WeeklyGrowth    0.032004 Surrogate Random Forest
 ProductFrequency    0.029238 Surrogate Random Forest
    ProductDemand    0.026677 Surrogate Random Forest
    RollingStd_30    0.025865 Surrogate Random Forest
            Lag_1    0.025846 Surrogate Random Forest
    RollingMedian    0.025529 Surrogate Random Forest
    RollingMean_3    0.025464 Surrogate Random Forest
    MonthlyGrowth    0.023266 Surrogate Random Forest
AverageOrderValue    0.022417 Surrogate Random Forest
```

### Permutation Importance
```
          feature  importance_mean  importance_std
           Lag_21         0.088903        0.027080
AverageOrderValue         0.012009        0.002572
       BasketSize         0.005941        0.002144
           Lag_14         0.003903        0.006570
            Lag_7         0.003740        0.012776
    ExpandingMean         0.003564        0.001657
        DayOfWeek         0.002965        0.001121
           Lag_90         0.002826        0.001998
     ExpandingStd         0.002466        0.001237
          Weekend         0.001451        0.000702
           Lag_30         0.001211        0.000842
           Lag_60         0.000812        0.002534
              Day         0.000549        0.002784
    CountryDemand         0.000482        0.000393
   CategoryDemand         0.000148        0.000185
```

### SHAP Summary
No rows available.

## Forecast Horizon Summary
```
 HorizonDays  ForecastDemand  ForecastRevenue
          30    28519.135372     26763.979790
          60    59151.350994     55590.114934
          90    91981.851268     86326.932228
         180   202051.295974    187124.142353
         365   488251.222756    441531.834887
```

## Visual Assets
Generated figures are available under `reports\figures`.
