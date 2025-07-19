import argparse

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import norm


def calculate_mean_post_review_time_for_treatment(
    df: pd.DataFrame, treatment_value: int
) -> float:
    """
    Calculate the mean post-review implementation time for a given AI treatment value.
    For example, if treatment_value is 0, this will return the mean post-review
    implementation time for issues where ai_treatment is 0.

    This is used to impute the post-review implementation time for issues where it is
    missing (12% of the data) -- as the mean post review time of the treatment group
    that issue is in.
    """
    filtered_issues = df[
        (df["ai_treatment"] == treatment_value)
        & (df["post_review_implementation_time"].notna())
    ]
    return filtered_issues["post_review_implementation_time"].mean()


def impute_missing_post_review_time_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Approx ~12% of the post-review implementation time is missing. We impute the review
    time on these issues as the mean post-review implementation time for the treatment
    group.

    See section 2.3 - Effect Estimation - of the paper for more details on this imputation,
    and C.3.4 - Non-robust outcome measure for details on other imputation methods tested.
    """

    # Calculate mean post-review implementation times for AI disallowed and allowed issues
    mean_post_review_times = {
        treatment: calculate_mean_post_review_time_for_treatment(df, treatment)
        for treatment in [0, 1]
    }

    # Impute missing post-review implementation times
    df.loc[
        df["post_review_implementation_time"].isna(),
        "post_review_implementation_time",
    ] = df["ai_treatment"].map(mean_post_review_times)

    return df


def add_total_implementation_time_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a total time column to the dataframe, which is the sum of the initial
    and post-review implementation times. This represents the total time taken
    by the developer to complete the issue.
    """
    df["total_implementation_time"] = (
        df["initial_implementation_time"] + df["post_review_implementation_time"]
    )
    return df


def run_regression(df: pd.DataFrame) -> tuple[float, dict[str, tuple[float, float]]]:
    """
    This function runs a regression to estimate the speedup of developers when
    they are using AI.

    See Appendix section D - Empirical Strategy in the paper for more details on
    the regression specification.

    This function implements stderr calculations including: non-robust, robust, and
    cluster-robust standard errors. The paper uses non-robust standard errors; for the
    core result, all three methods give similar results.
    """

    regression_formula = (
        "log_total_implementation_time ~ ai_treatment + log_predicted_time_no_ai"
    )

    # Convert columns to log
    df["log_total_implementation_time"] = np.log(df["total_implementation_time"])
    df["log_predicted_time_no_ai"] = np.log(df["predicted_time_no_ai"])

    # The various standard error specifications we want to run
    stderr_specs = [
        {
            "name": "Homoskedastic",
            "cov_type": "nonrobust",
            "cov_kwds": None,
        },
        {
            "name": "Robust (HC3)",
            "cov_type": "HC3",
            "cov_kwds": None,
        },
        {
            "name": "Clustered By Dev",
            "cov_type": "cluster",
            "cov_kwds": {"groups": df["dev_id"]},
        },
    ]

    cis: dict[str, tuple[float, float]] = {}
    for spec in stderr_specs:
        # Run the regression with the specified standard error specification
        model = smf.ols(regression_formula, data=df, missing="drop")
        res = model.fit(cov_type=spec["cov_type"], cov_kwds=spec["cov_kwds"])

        # Get the treatment effect coefficient and its standard error
        beta = res.params["ai_treatment"]
        se_beta = res.bse["ai_treatment"]

        # Per formula (5), convert βˆ to speedup
        # Note estimand is the same for every stderr specification
        estimand = np.exp(beta) - 1

        # Get the z-score for a 95% confidence interval
        z = norm.ppf(0.975)

        # CIs are βˆ − 1.96 · SE[βˆ], βˆ + 1.96 · SE[βˆ]
        beta_ci = (
            float(beta - z * se_beta),
            float(beta + z * se_beta),
        )

        # And then, we convert back to the speedup scale
        ci = (
            float(np.exp(beta_ci[0]) - 1),
            float(np.exp(beta_ci[1]) - 1),
        )

        cis[spec["name"]] = ci

    return estimand, cis


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-data", type=str, required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input_data)

    df = impute_missing_post_review_time_values(df)
    df = add_total_implementation_time_column(df)
    estimand, cis = run_regression(df)

    print(f"Regression calculated speedup of:          {round(estimand, 3)}")
    for name, ci in cis.items():
        print(
            f"CI calculed with stderr={name}:{' ' * (17 - len(name))} ({round(ci[0], 3)}, {round(ci[1], 3)})",
        )


if __name__ == "__main__":
    main()
