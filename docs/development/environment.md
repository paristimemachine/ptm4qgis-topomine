# Development

## Environment setup

Typically on Ubuntu:

```bash
# create virtual environment linking to system packages (for pyqgis)
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# bump dependencies inside venv
python -m pip install -U pip
python -m pip install -U -r requirements/development.txt

# install git hooks (pre-commit)
pre-commit install
```

## Resources

Interesting QGIS API documentation pages:

- <http://api.qgis.org/api/master/html/classQgisInterface.html>
- <http://python.qgis.org/api/core/Locator/QgsLocator.html>
- <http://python.qgis.org/api/core/Locator/QgsLocatorFilter.html>
