.PHONY: help

help: ## this help
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {sub("\\\\n",sprintf("\n%22c"," "), $$2);printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## insall python dependencies
	.venv/bin/pip install -Ur requirements.txt

run: ## run the script
	.venv/bin/python ./src/main.py
