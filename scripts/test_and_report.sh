#!/bin/bash

# Function to run tests with coverage
run_tests() {
    export TESTS_RUNNING="True"
    echo "yes" | coverage run --parallel-mode --concurrency=multiprocessing manage.py test --duration 5 --parallel $@
}

if run_tests --keepdb; then
    coverage combine
    coverage report
    exit 0
fi

echo "Tests failed with --keepdb flag. Retrying without it..."

# Run tests without extra flags if the first attempt failed
if run_tests; then
    coverage combine
    coverage report
    exit 0
fi

echo "Tests failed in both attempts."
exit 1
