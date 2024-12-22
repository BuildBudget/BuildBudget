---
title: "A $20,000 Workflow? Analyzing React Native's CI/CD Costs"
date: 2024-11-25
excerpt: "Analysis of an expensive workflow on an open-source project using BuildBudget"
---

While developing [BuildBudget](https://buildbudget.dev/) (currently in beta), a tool for analyzing GitHub Actions costs,
I discovered something surprising: the most expensive workflow among the top 10 GitHub organizations wasn't in a machine
learning repository training models on GPUs, nor in a complex monorepo building thousands of packages. It was React
Native's ["Test all" workflow](https://buildbudget.dev/demo/workflow/85394709/?start_date=2024-11-03&end_date=2024-12-03),
costing nearly $20,000 per month – with individual runs averaging $35.37, about 80 times more expensive than the typical
GitHub Actions workflow. You can explore all results yourself at [buildbudget.dev/demo](https://buildbudget.dev/demo).

## The Numbers That Caught My Eye

Let's look at what makes this workflow special:

- Average cost per run: $35.37
- Daily cost spikes up to $1,800
- Total workflow cost: $20,410.81 (in the analyzed 30-day period)
- Average execution time: 7:51:22
- Average billable time: 8:20:20

These numbers come from analyzing 562 workflow runs, with the vast majority triggered by pull requests. But what makes
this workflow so expensive?

[![React Native's "Test all" workflow stats](/static/images/workflow_dashboard_stats.png)](https://buildbudget.dev/demo/workflow/85394709/?start_date=2024-11-03&end_date=2024-12-03)
[![React Native's "Test all" workflow daily cost trend](/static/images/daily_cost_trend.png)](https://buildbudget.dev/demo/workflow/85394709/?start_date=2024-11-03&end_date=2024-12-03)

## The Perfect Storm: Matrices, macOS, and Minutes

### 1. The macOS Tax

The most expensive jobs in the workflow are iOS tests, costing up to $3.86 per run. While GitHub provides free
standard runners (ubuntu-latest) for public repositories, specialized runners like macos-13-large still incur costs –
about 10x more than standard Linux runners. What's interesting is that these expensive jobs have relatively low
execution rates (5.9%), suggesting the team is already trying to minimize their usage.

```yaml
test_e2e_ios_rntester:
  runs-on: macos-13-large
  strategy:
  matrix:
  jsengine: [ Hermes, JSC ]
  architecture: [ NewArch ]
  flavor: [ Debug, Release ]
```

### 2. The Matrix Multiplication

The workflow makes extensive use of matrix strategies, which can dramatically increase costs. Take the iOS tests above –
they run variations across:

- JavaScript engines (Hermes, JSC)
- Architecture (NewArch)
- Build type (Debug, Release)

This means a single change can trigger 2 × 1 × 2 = 4 parallel jobs, each on an expensive macOS runner. And that's just
one of many matrix configurations in the workflow.

As you can see in
the [workflow dashboard](https://buildbudget.dev/demo/workflow/85394709/?start_date=2024-11-03&end_date=2024-12-03),
there is a total of 79 jobs run as part of the workflow!


[![React Native's "Test all" workflow partial job analysis table](/static/images/job_analysis_partial.png)](https://buildbudget.dev/demo/workflow/85394709/?start_date=2024-11-03&end_date=2024-12-03)

### 3. The Minute Rounding Problem

GitHub Actions bills by rounding up to the nearest minute for each job. This creates an interesting cost dynamic with
matrices. Consider this example from the workflow:

```yaml
build_apple_slices_hermes:
  strategy:
    matrix:
      flavor: [ Debug, Release ]
      slice: [ macosx, iphoneos, iphonesimulator, appletvos, appletvsimulator, catalyst, xros, xrsimulator ]
```

This creates 16 parallel jobs. Even if each job takes only 30 seconds, you're billed for 16 minutes due to rounding.
Running these sequentially could theoretically reduce the billed time to just 1 minute.

## The Cost of Comprehensive Testing

Looking at React Native's workflow, it's clear that these costs aren't due to inefficiency – they're the price of
thorough testing across multiple platforms, architectures, and configurations. The workflow tests:

- Multiple JavaScript engines (Hermes, JSC)
- Different architectures (New Architecture, Old Architecture)
- Various build configurations (Debug, Release)
- Multiple platforms (iOS, Android)
- Different integration types (Static Libraries, Dynamic Frameworks)
- Various OS targets (macOS, iOS, tvOS, visionOS)

While standard Linux jobs are free for public repositories like React Native, the extensive use of specialized runners
for cross-platform testing drives up costs significantly. For private repositories, which most companies use,
understanding these costs becomes even more critical.

## Optimization Opportunities

While the high costs are justified by the project's needs, there are potential optimization strategies:

- Strategic Matrix Usage: Consider if all combinations in matrices are necessary. Could some combinations be tested less
  frequently?
- Sequential vs Parallel: For very short jobs, running them sequentially might be more cost-effective due to minute
  rounding.
- Conditional Testing: The workflow already shows signs of this with some jobs having low execution rates (5.7%).
  Further
  optimizing when comprehensive tests run could reduce costs.
- Runner Selection: The heavy use of macos-13-large runners contributes significantly to costs. Could some tests run on
  standard macOS runners?

## Beyond React Native

This analysis reveals broader insights about GitHub Actions costs:

- Matrix Awareness: While matrices are fantastic for comprehensive testing, their cost impact isn't always obvious. A
  simple 2×2×2 matrix means 8x the running costs.
- Platform Costs Matter: The choice of runner can have a 10x impact on costs. While standard runners are free for public
  repos, specialized runners and private repo usage require careful consideration of costs.
- The Rounding Effect: GitHub's per-minute billing with rounding up means parallel jobs can significantly increase costs
  for short-running tasks.

## Conclusion

React Native's workflow isn't expensive because it's inefficient – it's expensive because it's thorough. It's a reminder
that comprehensive testing across multiple platforms and configurations comes with real costs. Understanding these costs
helps teams make informed decisions about their CI/CD strategies.

While this workflow has higher costs than typical GitHub Actions workflows, it's worth noting that these costs are
relatively small compared to the developer time they save and the bugs they prevent in a framework used by thousands of
applications.

## Try BuildBudget

BuildBudget is currently in beta, and I'm actively working on new features to help teams optimize their GitHub Actions
costs. Future plans include:

- Automated implementation of cost improvements for workflows
- Cost comparisons and simulations across different runner providers
- More detailed cost analytics and optimization recommendations

Ready to analyze your own GitHub Actions costs? Visit buildbudget.dev to start using BuildBudget for free. You can
explore this React Native workflow analysis and more in our demo section.

Your feedback is valuable in shaping BuildBudget's development. Feel free to reach out with questions, suggestions, or
insights at <contact@buildbudget.dev>.

---

*Note: This analysis was conducted using BuildBudget, which estimates costs based on publicly available information and
best guesses for self-hosted runners. For precise cost tracking, organizations can use BuildBudget with their actual
runner costs.*
