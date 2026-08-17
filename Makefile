.PHONY: install data test run clean

install:
	python -m pip install -e .

data:
	python -m heatrisk.cli download

test:
	python -m unittest discover -s tests -v

run:
	python -m heatrisk.cli run

clean:
	rm -rf .cache outputs models

