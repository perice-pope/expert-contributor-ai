# CANARY_STRING_PLACEHOLDER

set -euo pipefail

# Create the workflow directory if it doesn't exist
mkdir -p /app/.github/workflows

# Write the complete GitHub Actions CI workflow
cat > /app/.github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [ main, master ]
    tags:
      - 'v*.*.*'  # Semver tags
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    name: Test (${{ matrix.os }}, Python ${{ matrix.python-version }}, Node.js ${{ matrix.node-version }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ['3.8', '3.9', '3.10']
        node-version: ['14', '16']
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Set up Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
      
      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: |
            ~/.cache/pip
            ${{ runner.os == 'Windows' && '~\AppData\Local\pip\Cache' || '' }}
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt', '**/pyproject.toml') }}
          restore-keys: |
            ${{ runner.os }}-pip-
      
      - name: Cache npm dependencies
        uses: actions/cache@v3
        with:
          path: |
            ~/.npm
            ${{ runner.os == 'Windows' && '~\AppData\Roaming\npm-cache' || '' }}
            node_modules
          key: ${{ runner.os }}-node-${{ matrix.node-version }}-${{ hashFiles('**/package-lock.json', '**/package.json') }}
          restore-keys: |
            ${{ runner.os }}-node-${{ matrix.node-version }}-
      
      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install --cache-dir ~/.cache/pip -r requirements.txt
        if: runner.os != 'Windows'
      
      - name: Install Python dependencies (Windows)
        run: |
          python -m pip install --upgrade pip
          pip install --cache-dir "%LOCALAPPDATA%\pip\Cache" -r requirements.txt
        if: runner.os == 'Windows'
      
      - name: Install Node.js dependencies
        run: |
          npm ci --cache ~/.npm --prefer-offline
        if: runner.os != 'Windows'
      
      - name: Install Node.js dependencies (Windows)
        run: |
          npm ci --cache "%APPDATA%\npm-cache" --prefer-offline
        if: runner.os == 'Windows'
      
      - name: Lint Python code
        run: |
          pylint src/ tests/ || true
          # Allow linting to pass even with warnings
      
      - name: Lint Node.js code
        run: |
          npm run lint || true
          # Allow linting to pass even with warnings
      
      - name: Run Python tests
        run: |
          pytest --cov=src --cov-report=xml --cov-report=term tests/
      
      - name: Run Node.js tests
        run: |
          npm test
      
      - name: Upload Python coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: python
          name: python-coverage-${{ matrix.os }}-${{ matrix.python-version }}
        continue-on-error: true
      
      - name: Upload Node.js coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage/coverage-final.json
          flags: nodejs
          name: nodejs-coverage-${{ matrix.os }}-${{ matrix.node-version }}
        continue-on-error: true
      
      - name: Upload coverage as artifact
        uses: actions/upload-artifact@v3
        with:
          name: coverage-${{ matrix.os }}-py${{ matrix.python-version }}-node${{ matrix.node-version }}
          path: |
            coverage.xml
            coverage/
          retention-days: 30
        continue-on-error: true
  
  publish:
    name: Publish to PyPI and npm
    runs-on: ubuntu-latest
    needs: test
    if: startsWith(github.ref, 'refs/tags/v') && github.event_name == 'push'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '16'
          registry-url: 'https://registry.npmjs.org'
      
      - name: Build Python package
        run: |
          python -m pip install --upgrade pip build
          python -m build
      
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
      
      - name: Publish to npm
        run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
EOF

echo "Workflow file created successfully"
