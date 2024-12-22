# Contributing to BuildBudget

First off, thank you for considering contributing to BuildBudget! It's people like you that help BuildBudget become a
better tool for understanding and optimizing GitHub Actions costs.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When
you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots if possible
* Include your environment details (OS, browser version, etc.)

### Suggesting Enhancements

If you have a suggestion for a new feature or enhancement, we'd love to hear it! Please provide the following
information:

* Use a clear and descriptive title
* Provide a detailed description of the proposed feature
* Explain why this enhancement would be useful to BuildBudget users
* List any alternatives you've considered
* Include mockups or examples if applicable

### Pull Requests

When submitting a pull request:

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. Ensure the test suite passes
4. Update the documentation if needed
5. Issue the pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/buildbudget.git

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest
```

## Styleguides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
* Consider starting the commit message with an applicable emoji:
    * 🎨 `:art:` when improving the format/structure of the code
    * 🐎 `:racehorse:` when improving performance
    * 📝 `:memo:` when writing docs
    * 🐛 `:bug:` when fixing a bug
    * 🔥 `:fire:` when removing code or files
    * ✅ `:white_check_mark:` when adding tests

### Python Styleguide

* Follow PEP 8
* Use type hints
* Write docstrings for all public methods
* Keep functions focused and small
* Use meaningful variable names

### JavaScript Styleguide

* Use ES6+ features
* Follow standard JavaScript conventions
* Use meaningful variable names
* Add comments for complex logic

### Tests

* Write test descriptions that explain what the test is verifying
* Keep tests focused and atomic
* Use meaningful test data
* Follow the Arrange-Act-Assert pattern

## Community

* Join our [Discussions](https://github.com/buildbudget/buildbudget/discussions)

## Questions?

Feel free to reach out to contact@buildbudget.dev with any questions about contributing.

Thank you for your interest in improving BuildBudget! ❤️
