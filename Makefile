# install dependencies
init:
	pip3 install -r requirements.txt
	pre-commit install

# stand up server to run API
run:
	./bin/run_coty

# run unit tests
test:
	python3 -m unittest discover -s tests/

# generate and show a code coverage report
coverage:
	coverage run --source=fantasy_coty -m unittest discover -s tests/
	coverage report

# lint using pycodestyle, pydocstyle and reformat with black
style:
	pycodestyle fantasy_coty
	pydocstyle fantasy_coty
	black fantasy_coty

clean:
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	rm -f .coverage
	rm -rf htmlcov/
