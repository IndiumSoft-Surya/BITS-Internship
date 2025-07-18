import numpy as np
from io import StringIO
import pandas as pd
import json


class eda:

    def generate_summary(self, df):
        null_like_values = ['Null', 'null', 'NULL', 'unknown', 'Unknown', 'UNKNOWN', 'NaN', 'nan', 'NAN']
        df.replace(null_like_values, np.nan, inplace=True)

        summary = {}

        # === Structured Data Info ===
        data_info = {
            "columns": [],
            "total_rows": len(df),
            "memory_usage": df.memory_usage(deep=True).sum()
        }

        for col in df.columns:
            data_info["columns"].append({
                "name": col,
                "non_null_count": df[col].notnull().sum(),
                "dtype": str(df[col].dtype)
            })

        summary["data_info"] = data_info

        # === Null Percentages ===
        null_percentages = (df.isnull().sum() / df.shape[0]) * 100
        summary["null_percentages"] = null_percentages.round(2).to_dict()

        # === Descriptive Statistics ===
        describe_df = df.describe().round(2)
        summary["descriptive_statistics"] = describe_df.to_dict()

        # === Correlation Matrix ===
        numeric_df = df.select_dtypes(include=np.number)
        correlation = numeric_df.corr().round(2)
        summary["correlation_matrix"] = correlation.to_dict()

        # === Skewness ===
        skewness = numeric_df.skew().round(2)
        summary["skewness"] = skewness.to_dict()


        # === Outlier Summary (IQR Method) ===
        outlier_summary = {}
        for col in numeric_df.columns:
            vals = df[col]
            mean_val = vals.mean()
            std_val = vals.std()

            df['z'] = (vals-mean_val)/std_val
            max_z_score = df['z'].max()

            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outlier_count = df[(df[col] < lower_bound) | (df[col] > upper_bound)].shape[0]
            outlier_summary[col] = {
                "Q1": round(Q1, 2),
                "Q3": round(Q3, 2),
                "IQR": round(IQR, 2),
                "outlier_count": outlier_count,
                "outlier_ratio": (outlier_count/(df[col].count())).round(2),
                "mean_val": mean_val.round(2),
                "std_val": std_val.round(2),
                "max_val": df[col].max(),
                "max_z_score": max_z_score.round(2)
            }
        summary["outlier_summary"] = outlier_summary
        df.drop(columns=['z'], inplace=True)

       # Unique Values Summary
        unique_values = {}
        for col in df.columns:
            try:
                unique_vals = df[col].dropna().unique()
                num_unique = len(unique_vals)

                # Determine column flag
                if df[col].isnull().all() or num_unique <= 1:
                    flag = "CONSTANT_OR_NULL"
                elif num_unique == df.shape[0]:
                    flag = "UNIQUE_ID"
                elif num_unique < 5:
                    flag = "LOW_CARDINALITY"
                elif num_unique > 50:
                    flag = "HIGH_CARDINALITY"
                else:
                    flag = "CATEGORICAL"

                unique_values[col] = {
                    "count": num_unique,
                    "flag": flag
                }
            except Exception as e:
                unique_values[col] = {"error": str(e)}

        summary["unique_values"] = unique_values


        # === Sample Data ===
        summary["sample_data"] = df.head().to_dict(orient="records")


        # === Final JSON Output ===
        file_like = StringIO(json.dumps(summary, separators=(',', ':'), default=str))

        return file_like
    