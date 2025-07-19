# Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity 

This repository contains anonymized data and the core regression functionality for the paper [Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity](https://arxiv.org/abs/2507.09089). 

See the [announcement](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) blog post for more information on the study.

# Replicating the core regression

First, install relevant dependencies:
```
pip install statsmodels==0.14.4 scipy==1.15.2
```

Then, run the regression:
```
python regression.py --input-data data_complete.csv
```

This should output:
```
Regression calculated speedup of: 0.188
CI calculed with stderr=Homoskedastic: (0.013, 0.395)
CI calculed with stderr=Robust (HC3): (0.013, 0.394)
CI calculed with stderr=Clustered By Dev: (0.016, 0.39)
```

Note that `0.188 = E(Time with AI) / E(Time without AI) - 1`. In other words, time with AI is greater than time without AI, or developers appear to be slowed down.

# Data Spec

`data_complete.csv` contains all valid issues completed by developers in the study. 
- `dev_id`: A unique integer identifying each developer. 
- `issue_id`: A unique integer identifying each issue. As there are 246 issues in this dataset, these are just `1, 2, ... 245, 246`.
- `predicted_time_no_ai`: How long (in minutes) the developer estimated the issues would take if they did not get AI access. Estimated pre-randomization.
- `predicted_time_ai_allowed`: How long (in minutes) the developer estimated the issues would take if they _did_ get AI access. Estimated pre-randomization.
- `Prior Task Exposure (1-5)`: How familiar the developer was with this type of task (1 is not familiar; 5 is very familiar). See more detail in appendix G.2.1 - Developer Instructions. Not present for all issues, as this started being collected halfway through the study.
- `External Resource Needs (1-3)`: How many external resources (e.g. docs) the developer expects to need to solve the issue (1 is no resources, 3 is many resources). See more detail in appendix G.2.1 - Developer Instructions. Not present for all issues, as this started being collected halfway through the study.
- `ai_treatment`: 0 if AI was allowed on this issue. 1 if AI was not allowed on this issue.
- `initial_implementation_time`: the time it took the developer to get up a pull-request for review. See more detail in appendix G.2.1 - Developer Instructions.
- `post_review_implementation_time`: the time it took the developer to fix up the PR before it was merged. Not present for all issues. See more detail in appendix G.2.1 - Developer Instructions. Not present for all data, as started being collected halfway through the study.