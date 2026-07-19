# Model Comparison Report

## Leaderboard
```
 accuracy  precision  recall       f1  balanced_accuracy      mcc  roc_auc   pr_auc  log_loss  brier_score          model_name           status     threshold  train_rows  validation_rows                                                                                                                           best_params reason
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.000001 0.000000e+00       Decision Tree        evaluated  1.000000e+00      2586.0            863.0                                                                                                                                   NaN    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.000001 0.000000e+00       Decision Tree tuned_randomized  1.000000e+00      2586.0            863.0                               {"classifier__min_samples_leaf": 8, "classifier__max_depth": 3, "classifier__class_weight": "balanced"}    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.000001 0.000000e+00       Decision Tree       tuned_grid  1.000000e+00      2586.0            863.0                                     {"classifier__class_weight": null, "classifier__max_depth": 4, "classifier__min_samples_leaf": 1}    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.001070 2.334311e-04       Random Forest        evaluated  9.880000e-01      2586.0            863.0                                                                                                                                   NaN    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.000978 2.220903e-04       Random Forest tuned_randomized  9.950000e-01      2586.0            863.0   {"classifier__n_estimators": 300, "classifier__min_samples_leaf": 2, "classifier__max_depth": 14, "classifier__class_weight": null}    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.000947 2.253838e-04       Random Forest       tuned_grid  9.975000e-01      2586.0            863.0 {"classifier__class_weight": null, "classifier__max_depth": null, "classifier__min_samples_leaf": 2, "classifier__n_estimators": 200}    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.003910 5.638998e-04         Extra Trees        evaluated  9.277433e-01      2586.0            863.0                                                                                                                                   NaN    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.004531 6.140348e-04         Extra Trees tuned_randomized  9.355486e-01      2586.0            863.0   {"classifier__n_estimators": 300, "classifier__min_samples_leaf": 2, "classifier__max_depth": 14, "classifier__class_weight": null}    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.002897 4.335458e-04         Extra Trees       tuned_grid  9.400000e-01      2586.0            863.0 {"classifier__class_weight": null, "classifier__max_depth": null, "classifier__min_samples_leaf": 1, "classifier__n_estimators": 200}    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.000020 6.123460e-10   Gradient Boosting        evaluated  9.999714e-01      2586.0            863.0                                                                                                                                   NaN    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.000002 9.867684e-12   Gradient Boosting tuned_randomized  9.999976e-01      2586.0            863.0                                      {"classifier__n_estimators": 250, "classifier__max_depth": 2, "classifier__learning_rate": 0.05}    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.022233 5.428336e-04   Gradient Boosting       tuned_grid  9.673237e-01      2586.0            863.0                                      {"classifier__learning_rate": 0.03, "classifier__max_depth": 2, "classifier__n_estimators": 100}    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.126928 1.420934e-02            AdaBoost        evaluated  8.807971e-01      2586.0            863.0                                                                                                                                   NaN    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.126928 1.420934e-02            AdaBoost tuned_randomized  8.807971e-01      2586.0            863.0                                                                    {"classifier__n_estimators": 50, "classifier__learning_rate": 0.3}    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.126928 1.420934e-02            AdaBoost       tuned_grid  8.807971e-01      2586.0            863.0                                                                   {"classifier__learning_rate": 0.5, "classifier__n_estimators": 100}    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.011165 3.452598e-03                 KNN tuned_randomized  8.571429e-01      2586.0            863.0                                                  {"classifier__weights": "uniform", "classifier__p": 1, "classifier__n_neighbors": 7}    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.012967 3.790967e-03                 KNN       tuned_grid  7.777778e-01      2586.0            863.0                                                  {"classifier__n_neighbors": 9, "classifier__p": 1, "classifier__weights": "uniform"}    NaN
 1.000000   1.000000     1.0 1.000000           1.000000 1.000000 1.000000 1.000000  0.080090 5.795451e-03         Naive Bayes        evaluated 2.036566e-284      2586.0            863.0                                                                                                                                   NaN    NaN
 0.998841   0.996528     1.0 0.998261           0.999132 0.997395 0.999964 0.999927  0.009562 1.944789e-03 Logistic Regression       tuned_grid  8.386439e-01      2586.0            863.0                                                                              {"classifier__C": 0.5, "classifier__class_weight": null}    NaN
 0.998841   0.996528     1.0 0.998261           0.999132 0.997395 0.999952 0.999902  0.008221 1.760997e-03 Logistic Regression tuned_randomized  9.325178e-01      2586.0            863.0                                                                        {"classifier__class_weight": "balanced", "classifier__C": 2.0}    NaN
```

## Tuning Summary
```
            model_name    search_strategy  best_score                                                                                                                           best_params
   Logistic Regression RandomizedSearchCV    1.000000                                                                        {"classifier__class_weight": "balanced", "classifier__C": 2.0}
   Logistic Regression       GridSearchCV    1.000000                                                                              {"classifier__C": 0.5, "classifier__class_weight": null}
         Decision Tree RandomizedSearchCV    1.000000                               {"classifier__min_samples_leaf": 8, "classifier__max_depth": 3, "classifier__class_weight": "balanced"}
         Decision Tree       GridSearchCV    1.000000                                     {"classifier__class_weight": null, "classifier__max_depth": 4, "classifier__min_samples_leaf": 1}
         Random Forest RandomizedSearchCV    1.000000   {"classifier__n_estimators": 300, "classifier__min_samples_leaf": 2, "classifier__max_depth": 14, "classifier__class_weight": null}
         Random Forest       GridSearchCV    1.000000 {"classifier__class_weight": null, "classifier__max_depth": null, "classifier__min_samples_leaf": 2, "classifier__n_estimators": 200}
           Extra Trees RandomizedSearchCV    1.000000   {"classifier__n_estimators": 300, "classifier__min_samples_leaf": 2, "classifier__max_depth": 14, "classifier__class_weight": null}
           Extra Trees       GridSearchCV    1.000000 {"classifier__class_weight": null, "classifier__max_depth": null, "classifier__min_samples_leaf": 1, "classifier__n_estimators": 200}
     Gradient Boosting RandomizedSearchCV    1.000000                                      {"classifier__n_estimators": 250, "classifier__max_depth": 2, "classifier__learning_rate": 0.05}
     Gradient Boosting       GridSearchCV    1.000000                                      {"classifier__learning_rate": 0.03, "classifier__max_depth": 2, "classifier__n_estimators": 100}
              AdaBoost RandomizedSearchCV    1.000000                                                                    {"classifier__n_estimators": 50, "classifier__learning_rate": 0.3}
              AdaBoost       GridSearchCV    1.000000                                                                   {"classifier__learning_rate": 0.5, "classifier__n_estimators": 100}
Support Vector Machine RandomizedSearchCV    1.000000                                                  {"classifier__kernel": "linear", "classifier__gamma": "scale", "classifier__C": 5.0}
Support Vector Machine       GridSearchCV    1.000000                                                  {"classifier__C": 0.5, "classifier__gamma": "scale", "classifier__kernel": "linear"}
                   KNN RandomizedSearchCV    0.997103                                                  {"classifier__weights": "uniform", "classifier__p": 1, "classifier__n_neighbors": 7}
                   KNN       GridSearchCV    0.997681                                                  {"classifier__n_neighbors": 9, "classifier__p": 1, "classifier__weights": "uniform"}
    MLP Neural Network RandomizedSearchCV    0.989522                                                                 {"classifier__hidden_layer_sizes": [64], "classifier__alpha": 0.0001}
    MLP Neural Network       GridSearchCV    0.989522                                                                 {"classifier__alpha": 0.0001, "classifier__hidden_layer_sizes": [64]}
```

## Explainability Tables
### Feature Importance
```
                     feature  importance  importance_percent
              CustomerTenure         0.0                 0.0
       DaysSinceLastPurchase         0.0                 0.0
            PurchaseMomentum         0.0                 0.0
        RevenueConcentration         0.0                 0.0
                RevenueTrend         0.0                 0.0
       RecentRevenueShare_90         0.0                 0.0
         RecentOrderCount_90         0.0                 0.0
       PreviousOrderCount_90         0.0                 0.0
       PreviousOrderCount_30         0.0                 0.0
 RollingPurchaseFrequency_60         0.0                 0.0
       PreviousOrderCount_60         0.0                 0.0
 RollingPurchaseFrequency_90         0.0                 0.0
        RollingBasketSize_90         0.0                 0.0
      RollingRevenueShare_90         0.0                 0.0
RollingPurchaseFrequency_180         0.0                 0.0
```

### Permutation Importance
```
                     feature  importance_mean  importance_std
        RollingBasketSize_90     5.018076e-01        0.008175
         RecentOrderCount_90     5.018076e-01        0.008175
      RollingRevenueShare_90     4.985129e-01        0.008309
       RecentRevenueShare_90     4.985129e-01        0.008309
       PreviousOrderCount_30     2.059452e-01        0.007787
 RollingPurchaseFrequency_60     4.913004e-02        0.002635
 RollingPurchaseFrequency_90     3.503214e-02        0.001551
        RecentOrderCount_180     8.871802e-03        0.001064
RollingPurchaseFrequency_180     5.191141e-03        0.000606
       PreviousOrderCount_60     4.275056e-03        0.000263
       PreviousOrderCount_90     8.383783e-04        0.000523
       DaysSinceLastPurchase     9.732726e-08        0.000312
            PurchaseMomentum     0.000000e+00        0.000000
              CustomerTenure    -2.092779e-04        0.000171
     RollingRevenueShare_180    -2.092779e-04        0.000171
```

### SHAP Summary
```
                     feature  mean_abs_shap status
        RollingBasketSize_90       0.501808  proxy
         RecentOrderCount_90       0.501808  proxy
      RollingRevenueShare_90       0.498513  proxy
       RecentRevenueShare_90       0.498513  proxy
       PreviousOrderCount_30       0.205945  proxy
 RollingPurchaseFrequency_60       0.049130  proxy
 RollingPurchaseFrequency_90       0.035032  proxy
        RecentOrderCount_180       0.008872  proxy
RollingPurchaseFrequency_180       0.005191  proxy
       PreviousOrderCount_60       0.004275  proxy
       PreviousOrderCount_90       0.000838  proxy
                RevenueTrend       0.000349  proxy
        RevenueConcentration       0.000279  proxy
       CustomerActivityScore       0.000279  proxy
              CustomerTenure       0.000209  proxy
```

### LIME Summary
No rows available.
