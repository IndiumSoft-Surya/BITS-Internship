import os
from textwrap import fill
import matplotlib.pyplot as plt
import seaborn as sns

class chart_plot:

    def gen_charts(self,response, df):

        categorical_features = response.get("categorical_features", [])
        numerical_features = response.get("numerical_features", [])
        target_col = response.get("target_col", "y")
        bivariate_pairs = response.get("bivariate_pairs", [])
        inference_univariate = response.get("inference_univariate", {})
        inference_bivariate = response.get("inference_bivariate", {})
        heatmap_inference = response.get("heatmap_inference", "")
        col_schema = response.get("col_schema", {})
        

        # Plot output directory-**
        plot_dir = "static/plots"
        os.makedirs(plot_dir, exist_ok=True)
        for f in os.listdir(plot_dir):
            os.remove(os.path.join(plot_dir, f))

        # Plotting
        sns.set_theme(style='whitegrid')

        # Univariate plots
        for col in numerical_features:
            if col not in df.columns: continue
            plt.figure(figsize=(10, 8))
            sns.histplot(df[col], kde=True, bins=30, color='#4C72B0')
            plt.title(f"Distribution of {col_schema.get(col, col)}")
            plt.xlabel(col_schema.get(col, col))
            plt.ylabel("Count")
            plt.text(0.5, -0.22, fill(inference_univariate.get(col, ''), 60),
                        transform=plt.gca().transAxes, ha='center', fontsize=10, color='dimgray')
            plt.tight_layout()
            plt.savefig(f"{plot_dir}/univariate_{col}.png", bbox_inches='tight')
            plt.close()

        for col in categorical_features:
            if col not in df.columns: continue
            plt.figure(figsize=(10, 8))
            sns.countplot(x=col, data=df, order=df[col].value_counts().index, palette='pastel')
            plt.title(f"Count of {col_schema.get(col, col)}")
            plt.xlabel(col_schema.get(col, col))
            plt.ylabel("Count")
            plt.xticks(rotation=30, ha='right')
            plt.text(0.5, -0.22, fill(inference_univariate.get(col, ''), 60),
                        transform=plt.gca().transAxes, ha='center', fontsize=10, color='dimgray')
            plt.tight_layout()
            plt.savefig(f"{plot_dir}/univariate_{col}.png", bbox_inches='tight')
            plt.close()

        # Bivariate plots
        for x, y in bivariate_pairs:
            if x not in df.columns or y not in df.columns: continue
            plt.figure(figsize=(10, 8))
            if x in numerical_features and y == target_col:
                sns.boxplot(x=df[y], y=df[x], palette='Set2')
            elif x in categorical_features and y == target_col:
                sns.barplot(x=df[x], y=df[y].map({'yes': 1, 'no': 0}), ci=None, palette='muted')
                plt.xticks(rotation=30, ha='right')
            elif x in numerical_features and y in numerical_features:
                sns.scatterplot(x=df[x], y=df[y], alpha=0.5)
            else:
                continue
            plt.title(f"{col_schema.get(x, x)} vs {col_schema.get(y, y)}")
            plt.xlabel(col_schema.get(x, x))
            plt.ylabel(col_schema.get(y, y))
            plt.text(0.5, -0.22, fill(inference_bivariate.get((x, y), ''), 60),
                        transform=plt.gca().transAxes, ha='center', fontsize=10, color='dimgray')
            plt.tight_layout()
            plt.savefig(f"{plot_dir}/bivariate_{x}_vs_{y}.png", bbox_inches='tight')
            plt.close()

        # Correlation heatmap
        corr_cols = [c for c in numerical_features if c in df.columns]
        if target_col in df.columns:
            corr = df[corr_cols + [target_col]].copy()
            corr[target_col] = corr[target_col].map({'yes': 1, 'no': 0})
            corrmat = corr.corr()
            plt.figure(figsize=(6, 5))
            sns.heatmap(corrmat, annot=True, fmt='.2f', cmap='coolwarm', square=True,
                        linewidths=0.5, annot_kws={'size': 10})
            plt.title("Correlation Heatmap")
            plt.text(0.5, -0.18, fill(heatmap_inference, 60), transform=plt.gca().transAxes,
                        ha='center', fontsize=10, color='dimgray')
            plt.tight_layout()
            plt.savefig(f"{plot_dir}/heatmap_correlation.png", bbox_inches='tight')
            plt.close()