# API Tests

Python tests for the API, done with [pytest](https://docs.pytest.org/)

## Run Locally

If you have yet to done so, clone the project

```bash
  git clone https://github.com/OMP404/PWP
```

Go to the project or tests directory

```bash
  cd PWP
```

Install dependencies

```bash
  pip install -r requirements.txt
```

Run all the tests with pytest

```bash
  pytest
```

Or if you want a specific test:

```bash
  pytest tests/test_file_name.py
```

e.g.

```bash
  pytest tests/test_basic_models.py
```

To generate a coverage report:

```bash
  pytest --cov --cov-report=html:directory_name
```

Coverage report can be found from \*directory_name/**index.html\***
