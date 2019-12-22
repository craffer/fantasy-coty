# install dependencies
init:
	pip3 install -r requirements.txt

# run on Delt W17, 2019 season
run:
	python3 fantasy_coty/main.py 1371476 2019

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
