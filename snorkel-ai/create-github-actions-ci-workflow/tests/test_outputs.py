"""Tests for GitHub Actions CI workflow creation task."""

import yaml
from pathlib import Path


def test_workflow_file_exists():
    """Test that the workflow file exists at the correct location."""
    workflow_path = Path("/app/.github/workflows/ci.yml")
    assert workflow_path.exists(), f"Workflow file {workflow_path} does not exist"


def test_workflow_is_valid_yaml():
    """Test that the workflow file is valid YAML."""
    workflow_path = Path("/app/.github/workflows/ci.yml")
    with open(workflow_path, 'r') as f:
        try:
            yaml.safe_load(f)
        except yaml.YAMLError as e:
            assert False, f"Workflow file is not valid YAML: {e}"


def test_workflow_has_matrix_build():
    """Test that the workflow contains a matrix build strategy with required OS and versions."""
    workflow_path = Path("/app/.github/workflows/ci.yml")
    with open(workflow_path, 'r') as f:
        content = f.read()
        workflow = yaml.safe_load(content)
    
    # Check that there's a job with a matrix strategy
    assert 'jobs' in workflow, "Workflow must have 'jobs' section"
    
    # Find a job with matrix strategy
    has_matrix = False
    matrix_config = None
    for job_name, job_config in workflow['jobs'].items():
        if 'strategy' in job_config and 'matrix' in job_config['strategy']:
            has_matrix = True
            matrix_config = job_config['strategy']['matrix']
            break
    
    assert has_matrix, "Workflow must have at least one job with a matrix strategy"
    
    # Check for required OS values
    assert 'os' in matrix_config, "Matrix must include 'os' key"
    assert 'ubuntu-latest' in matrix_config['os'], "Matrix must include 'ubuntu-latest'"
    assert 'windows-latest' in matrix_config['os'], "Matrix must include 'windows-latest'"
    
    # Check for required Python versions
    assert 'python-version' in matrix_config, "Matrix must include 'python-version' key"
    assert '3.8' in matrix_config['python-version'], "Matrix must include Python 3.8"
    assert '3.9' in matrix_config['python-version'], "Matrix must include Python 3.9"
    assert '3.10' in matrix_config['python-version'], "Matrix must include Python 3.10"
    
    # Check for required Node.js versions
    assert 'node-version' in matrix_config, "Matrix must include 'node-version' key"
    assert '14' in matrix_config['node-version'], "Matrix must include Node.js 14"
    assert '16' in matrix_config['node-version'], "Matrix must include Node.js 16"


def test_workflow_has_dependency_caching():
    """Test that the workflow implements caching for pip and npm dependencies."""
    workflow_path = Path("/app/.github/workflows/ci.yml")
    with open(workflow_path, 'r') as f:
        content = f.read()
        workflow = yaml.safe_load(content)
    
    # Check for caching actions
    has_pip_cache = False
    has_npm_cache = False
    
    for job_name, job_config in workflow['jobs'].items():
        if 'steps' in job_config:
            for step in job_config['steps']:
                if isinstance(step, dict):
                    uses = step.get('uses', '')
                    if 'actions/cache' in uses:
                        # Check if it's caching pip or npm
                        with_path = step.get('with', {}).get('path', '')
                        key = step.get('with', {}).get('key', '')
                        if 'pip' in key.lower() or 'pip' in str(with_path).lower():
                            has_pip_cache = True
                        if 'npm' in key.lower() or 'node' in key.lower() or 'npm' in str(with_path).lower() or 'node_modules' in str(with_path):
                            has_npm_cache = True
    
    assert has_pip_cache, "Workflow must cache pip dependencies using actions/cache"
    assert has_npm_cache, "Workflow must cache npm dependencies using actions/cache"


def test_workflow_has_linting_steps():
    """Test that the workflow includes linting steps for Python and Node.js."""
    workflow_path = Path("/app/.github/workflows/ci.yml")
    with open(workflow_path, 'r') as f:
        content = f.read()
        workflow = yaml.safe_load(content)
    
    has_python_lint = False
    has_nodejs_lint = False
    
    for job_name, job_config in workflow['jobs'].items():
        if 'steps' in job_config:
            for step in job_config['steps']:
                if isinstance(step, dict):
                    step_name = step.get('name', '').lower()
                    run_cmd = step.get('run', '').lower()
                    
                    # Check for Python linting
                    if 'lint' in step_name or 'pylint' in run_cmd or 'flake8' in run_cmd or 'ruff' in run_cmd:
                        if 'python' in step_name or 'pylint' in run_cmd or 'flake8' in run_cmd or 'ruff' in run_cmd:
                            has_python_lint = True
                    
                    # Check for Node.js linting
                    if 'lint' in step_name or 'eslint' in run_cmd:
                        if 'node' in step_name or 'eslint' in run_cmd or 'npm run lint' in run_cmd:
                            has_nodejs_lint = True
    
    assert has_python_lint, "Workflow must include Python linting step"
    assert has_nodejs_lint, "Workflow must include Node.js linting step"


def test_workflow_has_testing_steps():
    """Test that the workflow includes testing steps for Python and Node.js."""
    workflow_path = Path("/app/.github/workflows/ci.yml")
    with open(workflow_path, 'r') as f:
        content = f.read()
        workflow = yaml.safe_load(content)
    
    has_python_test = False
    has_nodejs_test = False
    
    for job_name, job_config in workflow['jobs'].items():
        if 'steps' in job_config:
            for step in job_config['steps']:
                if isinstance(step, dict):
                    step_name = step.get('name', '').lower()
                    run_cmd = step.get('run', '').lower()
                    
                    # Check for Python testing
                    if 'test' in step_name or 'pytest' in run_cmd:
                        if 'python' in step_name or 'pytest' in run_cmd:
                            has_python_test = True
                    
                    # Check for Node.js testing
                    if 'test' in step_name or 'npm test' in run_cmd or 'jest' in run_cmd:
                        if 'node' in step_name or 'npm test' in run_cmd or 'jest' in run_cmd:
                            has_nodejs_test = True
    
    assert has_python_test, "Workflow must include Python testing step"
    assert has_nodejs_test, "Workflow must include Node.js testing step"


def test_workflow_has_coverage_upload():
    """Test that the workflow includes coverage upload steps."""
    workflow_path = Path("/app/.github/workflows/ci.yml")
    with open(workflow_path, 'r') as f:
        content = f.read()
        workflow = yaml.safe_load(content)
    
    has_coverage_upload = False
    
    for job_name, job_config in workflow['jobs'].items():
        if 'steps' in job_config:
            for step in job_config['steps']:
                if isinstance(step, dict):
                    step_name = step.get('name', '').lower()
                    uses = step.get('uses', '').lower()
                    
                    # Check for coverage upload
                    if 'coverage' in step_name and ('upload' in step_name or 'codecov' in uses or 'coveralls' in uses):
                        has_coverage_upload = True
                    if 'codecov' in uses or 'coveralls' in uses:
                        has_coverage_upload = True
    
    assert has_coverage_upload, "Workflow must include coverage upload step"


def test_workflow_has_conditional_publishing():
    """Test that the workflow has conditional publishing on semver tags with secrets."""
    workflow_path = Path("/app/.github/workflows/ci.yml")
    with open(workflow_path, 'r') as f:
        content = f.read()
        workflow = yaml.safe_load(content)
    
    # Check for publish job
    has_publish_job = False
    publish_job = None
    
    for job_name, job_config in workflow['jobs'].items():
        if 'publish' in job_name.lower():
            has_publish_job = True
            publish_job = job_config
            break
    
    assert has_publish_job, "Workflow must have a publish job"
    
    # Check for conditional on semver tags
    assert 'if' in publish_job, "Publish job must have an 'if' condition"
    if_condition = publish_job['if']
    
    # Check for semver tag pattern (should check for tags starting with 'v')
    assert 'tags' in if_condition.lower() or 'refs/tags/v' in if_condition or 'startsWith' in if_condition, \
        "Publish job must be conditional on semver tags (refs/tags/v*)"
    
    # Check for PyPI publishing with secret
    has_pypi_publish = False
    has_npm_publish = False
    has_pypi_secret = False
    has_npm_secret = False
    
    if 'steps' in publish_job:
        for step in publish_job['steps']:
            if isinstance(step, dict):
                step_name = step.get('name', '').lower()
                uses = step.get('uses', '').lower()
                run_cmd = step.get('run', '').lower()
                env = step.get('env', {})
                with_params = step.get('with', {})
                
                # Check for PyPI publishing
                if 'pypi' in step_name or 'pypa' in uses or 'pypi' in uses:
                    has_pypi_publish = True
                    # Check for secret
                    if 'PYPI' in str(with_params) or 'PYPI' in str(env) or 'secrets.PYPI' in str(step):
                        has_pypi_secret = True
                
                # Check for npm publishing
                if 'npm' in step_name and 'publish' in step_name or 'npm publish' in run_cmd:
                    has_npm_publish = True
                    # Check for secret
                    if 'NPM' in str(env) or 'secrets.NPM' in str(step) or 'NODE_AUTH_TOKEN' in str(env):
                        has_npm_secret = True
    
    assert has_pypi_publish, "Publish job must include PyPI publishing step"
    assert has_npm_publish, "Publish job must include npm publishing step"
    assert has_pypi_secret, "PyPI publishing must use encrypted secret (PYPI_API_TOKEN)"
    assert has_npm_secret, "npm publishing must use encrypted secret (NPM_TOKEN)"


def test_workflow_has_required_triggers():
    """Test that the workflow has appropriate triggers (push, pull_request, tags)."""
    workflow_path = Path("/app/.github/workflows/ci.yml")
    with open(workflow_path, 'r') as f:
        content = f.read()
        workflow = yaml.safe_load(content)
    
    # YAML parses 'on:' as True (boolean), so check for either 'on' or True
    triggers = workflow.get('on') or workflow.get(True) or workflow.get('On')
    assert triggers is not None, "Workflow must have 'on' section for triggers"
    
    # Check for push trigger
    assert 'push' in triggers, "Workflow must trigger on push events"
    
    # Check for pull_request trigger
    assert 'pull_request' in triggers, "Workflow must trigger on pull_request events"
    
    # Check for tags trigger (for semver publishing)
    if isinstance(triggers.get('push'), dict):
        assert 'tags' in triggers['push'], "Workflow should trigger on tags for publishing"
