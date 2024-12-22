# BuildBudget

BuildBudget helps teams understand and optimize their GitHub Actions costs. Get detailed insights into CI/CD spending
across repositories, workflows, and jobs, whether using GitHub-hosted or self-hosted runners.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Features

- **Usage Analytics**: View detailed breakdowns of GitHub Actions usage by repository, organization, workflow, and job
- **Cost Estimation**: Get accurate cost estimates for GitHub-hosted runners and compare with alternative providers
- **Spending Analysis**: Identify your most resource-intensive workflows and jobs
- **Cross-Platform Support**: Works with both GitHub.com and GitHub Enterprise Server
- **Self-Hosted Option**: Deploy and run BuildBudget in your own infrastructure

## Getting Started

### GitHub.com Setup

1. Install the BuildBudget app from the GitHub Marketplace for your organization or specific repositories
2. BuildBudget will start receiving webhook events automatically
3. Access your dashboard to view insights and cost analysis

### GitHub Enterprise Server Setup

1. Clone this repository
2. Follow the [deployment guide](docs/deployment.md) to set up BuildBudget in your infrastructure
3. Configure a global webhook in your GitHub Enterprise Server to send events to BuildBudget
4. Access your dashboard to view insights and cost analysis

## Demo

Check out our [live demo](https://buildbudget.dev/demo) featuring an analysis of GitHub's most popular orgs.

## Development

```bash
# Clone the repository
git clone https://github.com/username/buildbudget.git

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a Pull Request.

## License

BuildBudget is open-source software licensed under the [Apache License 2.0](LICENSE).

## Support

While BuildBudget is open-source, its development and maintenance require significant effort. If you find it valuable,
consider:

- Starring the repository
- Sharing your experience with others
- [Contributing](#contributing) to the project
- Reaching out for enterprise support at contact@buildbudget.dev

## Further Reading

- [Deployment Guide](docs/deployment.md)

## Example Use Cases

- [A $20,000 Workflow? Analyzing React Native's CI/CD Costs](https://buildbudget.dev/blog/test-all-workflow/)
- More case studies coming soon...

## About

BuildBudget was created by [Edu Ramírez](https://www.linkedin.com/in/eduramirez/). It was born out of the need for
better control over GitHub Actions spending in large organizations.
