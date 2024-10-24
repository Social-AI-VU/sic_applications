echo "Installing package and development dependencies..."
pip install -e ../.[dev]

echo "Installing pre-commit hooks..."
pre-commit install

echo "Running pre-commit checks on all files..."
pre-commit run --all-files

echo "Fix complete!"
