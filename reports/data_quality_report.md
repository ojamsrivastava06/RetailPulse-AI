# Data Quality Report

## Overview
- Rows: 400916
- Columns: 38
- Duplicate records: 0
- Invalid quantities: 0
- Invalid prices: 0

## Missing Values
- No missing values detected.

## Data Types
- InvoiceNo: str
- StockCode: object
- Description: str
- Quantity: int64
- InvoiceDate: datetime64[us]
- UnitPrice: float64
- CustomerID: float64
- Country: str
- TotalSales: float64
- Year: int32
- Month: int32
- Week: int64
- Quarter: int32
- Day: int32
- Hour: int32
- DayOfWeek: str
- IsWeekend: int64
- IsMonthStart: int64
- IsMonthEnd: int64
- Season: str
- Revenue: float64
- Profit: float64
- InvoiceRevenue: float64
- BasketSize: int64
- InvoiceCountry: str
- InvoiceCustomerID: float64
- FirstInvoiceDate: datetime64[us]
- AverageBasketValue: float64
- CLV: float64
- CustomerTenure: int64
- CustomerFrequency: float64
- DaysSinceLastPurchase: int64
- MonthlyRevenue: float64
- MonthlyOrderCount: int64
- CountryRevenue: float64
- ProductFrequency: int64
- AverageOrderValue: float64
- ProductCategory: str

## Summary Statistics
- Quantity: mean=13.77, std=97.64, min=1.00, max=19152.00
- UnitPrice: mean=3.31, std=35.05, min=0.00, max=10953.50
- CustomerID: mean=15361.54, std=1680.64, min=12346.00, max=18287.00
- TotalSales: mean=21.95, std=77.76, min=0.00, max=15818.40
- Year: mean=2009.92, std=0.26, min=2009.00, max=2010.00
- Month: mean=7.40, std=3.47, min=1.00, max=12.00
- Week: mean=30.00, std=15.04, min=1.00, max=52.00
- Quarter: mean=2.78, std=1.14, min=1.00, max=4.00
- Day: mean=15.37, std=8.74, min=1.00, max=31.00
- Hour: mean=12.87, std=2.31, min=7.00, max=20.00
- IsWeekend: mean=0.18, std=0.38, min=0.00, max=1.00
- IsMonthStart: mean=0.04, std=0.18, min=0.00, max=1.00
- IsMonthEnd: mean=0.03, std=0.18, min=0.00, max=1.00
- Revenue: mean=21.95, std=77.76, min=0.00, max=15818.40
- Profit: mean=6.58, std=23.33, min=0.00, max=4745.52
- InvoiceRevenue: mean=657.23, std=1286.65, min=0.84, max=44051.60
- BasketSize: mean=42.81, std=34.13, min=1.00, max=251.00
- InvoiceCustomerID: mean=15361.54, std=1680.64, min=12346.00, max=18287.00
- AverageBasketValue: mean=21.95, std=68.05, min=0.55, max=10953.50
- CLV: mean=11388.41, std=33206.05, min=2.95, max=349164.35
- CustomerTenure: mean=245.20, std=124.07, min=1.00, max=374.00
- CustomerFrequency: mean=0.16, std=0.33, min=0.01, max=4.00
- DaysSinceLastPurchase: mean=161.35, std=113.40, min=0.00, max=373.00
- MonthlyRevenue: mean=1502.37, std=3690.83, min=1.25, max=52609.31
- MonthlyOrderCount: mean=2.53, std=3.79, min=1.00, max=40.00
- CountryRevenue: mean=6722253.23, std=2078141.33, min=140.39, max=7381644.43
- ProductFrequency: mean=333.84, std=368.42, min=1.00, max=3021.00
- AverageOrderValue: mean=657.23, std=1286.65, min=0.84, max=44051.60

## Outlier Notes
- Revenue outliers detected via IQR rule: 33843
- Outliers were reviewed using value range checks for revenue, quantity, and unit price.
- Extreme values are retained when they represent valid transactions; they are flagged for further review.