

test_run:
	py.test -v tests


release:
	rm -rf dist
	mkdir dist
	python setup.py sdist bdist_wheel
	python -m twine upload dist/*

clean:
	find . -name __pycache__ -exec rm -rf {} +
