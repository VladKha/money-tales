.PHONY: setup

setup: create_venv install_requirements

create_venv:
	@echo "Creating Python virtual environment..."
	python -m venv .venv
	source .venv/bin/activate

install_requirements:
	@echo "Installing requirements..."
	pip install -r requirements.txt

generate_rss_feed:
	@echo "Generating RSS feed..."
	python src/generate_rss.py

run_ui:
	@echo "Starting Gradio UI..."
	python gradio_ui.py