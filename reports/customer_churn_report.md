# Customer Churn Report

## Overview
RetailPulse Phase 5 builds a customer churn and retention intelligence layer on top of the curated transactional dataset. The workflow creates churn labels for 30, 60, 90, and 180 day windows, benchmarks a model zoo, calibrates probabilities, and assigns retention recommendations.

## Best Model
- Selected model: **Naive Bayes**
- Threshold: **0.000**
- Customer rows: **4,312**
- Churn rate: **33.28%**

## Model Leaderboard
```
 accuracy  precision  recall  f1  balanced_accuracy  mcc  roc_auc  pr_auc  log_loss  brier_score        model_name           status  threshold  train_rows  validation_rows                                                                                                                           best_params reason
      1.0        1.0     1.0 1.0                1.0  1.0      1.0     1.0  0.000001 0.000000e+00     Decision Tree        evaluated   1.000000      2586.0            863.0                                                                                                                                   NaN    NaN
      1.0        1.0     1.0 1.0                1.0  1.0      1.0     1.0  0.000001 0.000000e+00     Decision Tree tuned_randomized   1.000000      2586.0            863.0                               {"classifier__min_samples_leaf": 8, "classifier__max_depth": 3, "classifier__class_weight": "balanced"}    NaN
      1.0        1.0     1.0 1.0                1.0  1.0      1.0     1.0  0.000001 0.000000e+00     Decision Tree       tuned_grid   1.000000      2586.0            863.0                                     {"classifier__class_weight": null, "classifier__max_depth": 4, "classifier__min_samples_leaf": 1}    NaN
      1.0        1.0     1.0 1.0                1.0  1.0      1.0     1.0  0.001070 2.334311e-04     Random Forest        evaluated   0.988000      2586.0            863.0                                                                                                                                   NaN    NaN
      1.0        1.0     1.0 1.0                1.0  1.0      1.0     1.0  0.000978 2.220903e-04     Random Forest tuned_randomized   0.995000      2586.0            863.0   {"classifier__n_estimators": 300, "classifier__min_samples_leaf": 2, "classifier__max_depth": 14, "classifier__class_weight": null}    NaN
      1.0        1.0     1.0 1.0                1.0  1.0      1.0     1.0  0.000947 2.253838e-04     Random Forest       tuned_grid   0.997500      2586.0            863.0 {"classifier__class_weight": null, "classifier__max_depth": null, "classifier__min_samples_leaf": 2, "classifier__n_estimators": 200}    NaN
      1.0        1.0     1.0 1.0                1.0  1.0      1.0     1.0  0.003910 5.638998e-04       Extra Trees        evaluated   0.927743      2586.0            863.0                                                                                                                                   NaN    NaN
      1.0        1.0     1.0 1.0                1.0  1.0      1.0     1.0  0.004531 6.140348e-04       Extra Trees tuned_randomized   0.935549      2586.0            863.0   {"classifier__n_estimators": 300, "classifier__min_samples_leaf": 2, "classifier__max_depth": 14, "classifier__class_weight": null}    NaN
      1.0        1.0     1.0 1.0                1.0  1.0      1.0     1.0  0.002897 4.335458e-04       Extra Trees       tuned_grid   0.940000      2586.0            863.0 {"classifier__class_weight": null, "classifier__max_depth": null, "classifier__min_samples_leaf": 1, "classifier__n_estimators": 200}    NaN
      1.0        1.0     1.0 1.0                1.0  1.0      1.0     1.0  0.000020 6.123460e-10 Gradient Boosting        evaluated   0.999971      2586.0            863.0                                                                                                                                   NaN    NaN
      1.0        1.0     1.0 1.0                1.0  1.0      1.0     1.0  0.000002 9.867684e-12 Gradient Boosting tuned_randomized   0.999998      2586.0            863.0                                      {"classifier__n_estimators": 250, "classifier__max_depth": 2, "classifier__learning_rate": 0.05}    NaN
      1.0        1.0     1.0 1.0                1.0  1.0      1.0     1.0  0.022233 5.428336e-04 Gradient Boosting       tuned_grid   0.967324      2586.0            863.0                                      {"classifier__learning_rate": 0.03, "classifier__max_depth": 2, "classifier__n_estimators": 100}    NaN
```

## Hyperparameter Tuning
```
         model_name    search_strategy  best_score                                                                                                                           best_params
Logistic Regression RandomizedSearchCV         1.0                                                                        {"classifier__class_weight": "balanced", "classifier__C": 2.0}
Logistic Regression       GridSearchCV         1.0                                                                              {"classifier__C": 0.5, "classifier__class_weight": null}
      Decision Tree RandomizedSearchCV         1.0                               {"classifier__min_samples_leaf": 8, "classifier__max_depth": 3, "classifier__class_weight": "balanced"}
      Decision Tree       GridSearchCV         1.0                                     {"classifier__class_weight": null, "classifier__max_depth": 4, "classifier__min_samples_leaf": 1}
      Random Forest RandomizedSearchCV         1.0   {"classifier__n_estimators": 300, "classifier__min_samples_leaf": 2, "classifier__max_depth": 14, "classifier__class_weight": null}
      Random Forest       GridSearchCV         1.0 {"classifier__class_weight": null, "classifier__max_depth": null, "classifier__min_samples_leaf": 2, "classifier__n_estimators": 200}
        Extra Trees RandomizedSearchCV         1.0   {"classifier__n_estimators": 300, "classifier__min_samples_leaf": 2, "classifier__max_depth": 14, "classifier__class_weight": null}
        Extra Trees       GridSearchCV         1.0 {"classifier__class_weight": null, "classifier__max_depth": null, "classifier__min_samples_leaf": 1, "classifier__n_estimators": 200}
  Gradient Boosting RandomizedSearchCV         1.0                                      {"classifier__n_estimators": 250, "classifier__max_depth": 2, "classifier__learning_rate": 0.05}
  Gradient Boosting       GridSearchCV         1.0                                      {"classifier__learning_rate": 0.03, "classifier__max_depth": 2, "classifier__n_estimators": 100}
           AdaBoost RandomizedSearchCV         1.0                                                                    {"classifier__n_estimators": 50, "classifier__learning_rate": 0.3}
           AdaBoost       GridSearchCV         1.0                                                                   {"classifier__learning_rate": 0.5, "classifier__n_estimators": 100}
```

## Important Feature Interpretation
- **CustomerTenure**: This feature contributes to churn and retention modeling.
- **DaysSinceLastPurchase**: Customers with a longer pause since their last order are more likely to churn.
- **PurchaseMomentum**: Momentum compares recent buying to the prior observation window.
- **RevenueConcentration**: Highly concentrated revenue can expose a customer to seasonal or one-off demand.
- **RevenueTrend**: Revenue trend signals whether wallet share is strengthening or fading.
- **RecentRevenueShare_90**: This feature contributes to churn and retention modeling.
- **RecentOrderCount_90**: This feature contributes to churn and retention modeling.
- **PreviousOrderCount_90**: This feature contributes to churn and retention modeling.
- **PreviousOrderCount_30**: This feature contributes to churn and retention modeling.
- **RollingPurchaseFrequency_60**: This feature contributes to churn and retention modeling.
- **PreviousOrderCount_60**: This feature contributes to churn and retention modeling.
- **RollingPurchaseFrequency_90**: Recent order cadence is a direct signal of customer stickiness.

## Probability and Risk Snapshot
```
 CustomerID  ChurnProbability  RetentionProbability RiskCategory  CustomerHealthScore
      18102          0.010538              0.989462          Low                99.07
      14646          0.028298              0.971702          Low                95.98
      14156          0.021626              0.978374          Low                97.09
      14911          0.009702              0.990298          Low                99.16
      13694          0.025890              0.974110          Low                96.35
      17511          0.019418              0.980582          Low                97.88
      15061          0.015986              0.984014          Low                98.18
      16684          0.040618              0.959382          Low                94.13
      16754          0.029778              0.970222          Low                96.37
      17949          0.022350              0.977650          Low                97.01
      13089          0.017866              0.982134          Low                97.76
      15311          0.010170              0.989830          Low                99.12
```

## Visual Assets
Generated figures are stored in `project\retailpulse-main\reports\figures`.
