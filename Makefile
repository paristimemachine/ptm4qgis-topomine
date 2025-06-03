.PHONY: install
install: ## Install the dependencies
	@pip install -U pip setuptools wheel
	@pip install -U -r requirements/development.txt
	@pip install -U -r requirements/documentation.txt
	@pip install -U -r requirements/packaging.txt
	@pip install -U -r requirements/testing.txt

.PHONY: docs
docs: ## Compile the docs
	@sphinx-build -b html docs docs/_build/html

.PHONY: docs-optimized
docs-optimized: ## Compile the docs (optimized)
	@sphinx-build -b html -d docs/_build/cache -j auto -q docs docs/_build/html

.PHONY: docs-live
docs-live: ## Live rendering of the docs
	@sphinx-autobuild -b html docs/ docs/_build
