.PHONY: setup

setup: create_venv install_requirements

create_venv:
	@echo "Creating Python virtual environment..."
	python3 -m venv .venv

install_requirements:
	@echo "Installing requirements..."
	.venv/bin/pip install -r requirements.txt 

run_ui:
	@echo "Starting Gradio UI..."
	python gradio_ui.py