# Model Leaderboard

## Ranked Models
```
           model_name configuration  series_count        mae       rmse         mape      smape           r2      mase  selection_eligible
         Holt-Winters       default             5 195.037128 404.386716  4996.838273 111.035000    -6.428141  2.209167                True
                  MLP       default             5 193.841107 408.279667  5301.282766 120.369011    -7.588638  2.518206                True
                ARIMA       default             5 190.483489 408.425695  5501.740423 119.024702    -4.228452  2.055137                True
Exponential Smoothing       default             5 171.681479 409.102155  4128.616104 117.892903    -3.997407  1.982601                True
               SARIMA       default             5 197.052031 409.412104  5597.012640 120.342533    -9.517294  2.659833                True
           ElasticNet         tuned             5 210.700622 412.668356  5312.507867 128.027713   -15.462613  3.150649                True
                  MLP         tuned             5 204.020855 435.734006  5399.558204 122.692945   -12.620246  2.972732                True
       Moving Average       default             5 294.186545 453.579838  9324.281361 130.363598    -0.773778  1.469888                True
                Naive       default             5 236.391111 460.871042  4516.200385 112.864202    -0.616076  1.009523                True
             AdaBoost       default             5 212.504301 467.484795  6999.422713 119.136306  -609.133524 11.584877                True
           ElasticNet       default             5 272.410812 485.113294  7514.032503 134.837559   -26.492834  4.037280                True
                Ridge       default             5 273.255613 486.038785  7562.844711 134.771619   -26.819220  4.048238                True
    Gradient Boosting       default             5 271.195357 493.309870  9538.314953 122.077289   -15.074921  2.944326                True
          Extra Trees       default             5 315.289904 552.272967  9557.330250 120.518429    -9.499287  2.829413                True
        Random Forest       default             5 399.590787 554.602739 15500.801223 129.093371   -79.119605  6.148338                True
             AdaBoost         tuned             5 285.499269 594.128658 11437.016136 118.102066 -1026.800336 16.545071                True
                 Holt       default             5 507.026217 629.875478 19207.013664 117.178213    -2.122447  1.755931                True
        Decision Tree       default             5 399.260996 703.809677 10531.000931 111.147291   -84.116978  3.921404                True
       Seasonal Naive       default             5 359.602222 756.937521  7858.959854  89.406088    -7.978324  1.731741                True
                Lasso       default             5 496.990639 776.769404 17515.258421 142.085355   -32.474838  4.849003                True
```

## Tuning Summary
```
model_name search_strategy  selected_feature_count  best_rmse                                                                     best_params
  AdaBoost            grid                      20 141.507229                                    {"learning_rate": 0.05, "n_estimators": 100}
       MLP          random                      20 155.259973 {"alpha": 0.0005, "hidden_layer_sizes": [128, 64], "learning_rate_init": 0.005}
ElasticNet            grid                      20 172.681426                                                 {"alpha": 0.1, "l1_ratio": 0.2}
```
