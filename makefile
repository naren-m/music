# Set up virtual environment
venv:
	python3 -m venv .venv
	. .venv/bin/activate

# Enable virtual environment
activate:
	. .venv/bin/activate

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests and generate coverage report
test:
	pytest --cov-report html --cov=. tests/

# Format code using yapf
format:
	yapf -i ./*.py

# Clean up generated files
clean:
	rm -rf .coverage htmlcov

# Default target
all: venv-activate install test
