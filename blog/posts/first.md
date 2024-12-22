---
title: "Introducing BuildBudget"
date: 2024-11-25
excerpt: "BuildBudget is a tool designed to help teams understand and optimize their costs when using GitHub Actions"
---

BuildBudget is a tool designed to help teams understand and optimize their costs when using GitHub Actions. By
providing clear visibility into spending, identifying inefficiencies, and offering guidance on optimization
strategies, BuildBudget enables teams to reduce their CI/CD costs without compromising on performance. Created
by [Edu Ramírez](https://www.linkedin.com/in/eduramirez/), a backend engineer with over 10 years of
experience, BuildBudget was born out of the need for better control over CI/CD spending.

## The Story Behind BuildBudget

While working for a large company, Edu witnessed firsthand the challenges of managing costs associated with
GitHub Actions. As teams migrated to the platform, it became clear that there was a lack of adequate tools to
understand and optimize spending. Despite investing tens of thousands of euros in CI/CD, inefficiencies such as
over-provisioned resources, excessive scheduled tasks, and redundant tasks went unnoticed.

Determined to tackle this problem, Edu developed BuildBudget to provide teams with clear visibility into
their GitHub Actions costs, whether using GitHub-hosted or self-hosted runners. By identifying inefficiencies
and guiding users on optimization strategies, BuildBudget aims to help teams reduce their CI/CD spending without
compromising on performance.

## How BuildBudget Works

BuildBudget seamlessly integrates with your GitHub repositories by setting up a webhook to receive workflow_job
and workflow_run events. For GitHub.com users, getting started is as simple as installing the BuildBudget app
from the GitHub Marketplace for the desired organization or specific repositories. GitHub Enterprise Server
users can set up a global webhook to send data to BuildBudget.

Once set up, BuildBudget provides comprehensive insights into your GitHub Actions usage and costs. It goes beyond
the basic features offered by GitHub's UI, focusing on cost reduction, analyzing large amounts of repositories
and organizations, and providing cost estimations for different runner providers. BuildBudget also makes the
distinction between execution times and billable time explicit, helping you understand the true cost of your
CI/CD pipeline.

## The Future of BuildBudget

In the short term, BuildBudget aims to provide even better tools for visualizing workflow inefficiencies. This
includes identifying issues such as overly complex workflows with more jobs than needed, redundant tasks in pull
requests, poorly managed scheduled tasks, and the impact of caching strategies. By guiding users on actions to
tackle these issues, BuildBudget strives to maximize cost savings.

Additionally, BuildBudget plans to introduce a feature that allows users to estimate the costs of using different
runner providers, empowering teams to make informed decisions about their CI/CD infrastructure.

Looking further ahead, the vision for BuildBudget is to automate optimization as much as possible. This includes
generating automated pull requests that optimize workflows and provide explanations of the impact of the
changes, making it even easier for teams to continuously improve their CI/CD processes and manage costs
effectively.

## About the Founder

[Edu Ramírez](https://www.linkedin.com/in/eduramirez/) is a backend engineer with over a decade of experience,
specializing in CI/CD and platform development. Through his work at a leading global company, Edu gained deep insights
into the challenges of managing GitHub Actions costs at scale. Driven by a passion for efficiency and optimization, he
created BuildBudget to help teams unlock the full potential of GitHub Actions while keeping costs under control.
