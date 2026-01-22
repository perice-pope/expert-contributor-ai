# CANARY_STRING_PLACEHOLDER
"""Pylint plugin to detect blocking I/O in async functions."""
import astroid
import toml
from pathlib import Path
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter


class AsyncIOChecker(BaseChecker):
    """Checker for blocking I/O operations in async functions."""
    name = "async-io-checker"
    priority = -1
    msgs = {
        "E9001": (
            "Blocking I/O call '%s' in async function. Consider wrapping with 'await asyncio.to_thread(...)'",
            "blocking-io-in-async",
            "Blocking I/O detected in async context",
        ),
    }
    
    def __init__(self, linter: PyLinter):
        super().__init__(linter)
        self._load_config()
    
    def _load_config(self):
        """Load configuration from pyproject.toml."""
        self.blocking_functions = ["open", "time.sleep", "requests.get", "requests.post", "urllib.request.urlopen"]
        self.enabled = True
        
        # Try to read pyproject.toml
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.exists():
            pyproject_path = Path("/app/pyproject.toml")
        
        if pyproject_path.exists():
            try:
                config = toml.load(pyproject_path)
                checker_config = config.get("tool", {}).get("pylint", {}).get("async_io_checker", {})
                
                if "blocking_functions" in checker_config:
                    self.blocking_functions = checker_config["blocking_functions"]
                if "enabled" in checker_config:
                    self.enabled = checker_config["enabled"]
            except Exception:
                pass
    
    def visit_functiondef(self, node: astroid.FunctionDef):
        """Visit function definitions."""
        if not self.enabled:
            return
        
        if not self._is_async_function(node):
            return
        
        self._check_node(node.body, node)
    
    def visit_asyncfunctiondef(self, node: astroid.AsyncFunctionDef):
        """Visit async function definitions."""
        if not self.enabled:
            return
        
        self._check_node(node.body, node)
    
    def _is_async_function(self, node):
        """Check if a function is async."""
        if isinstance(node, astroid.AsyncFunctionDef):
            return True
        if isinstance(node, astroid.FunctionDef) and node.is_async:
            return True
        return False
    
    def _check_node(self, nodes, func_node):
        """Recursively check nodes for blocking I/O calls."""
        for node in nodes:
            if isinstance(node, astroid.Call):
                self._check_blocking_call(node, func_node)
            elif isinstance(node, (astroid.If, astroid.For, astroid.While, astroid.With)):
                # Recursively check nested blocks
                if hasattr(node, "body"):
                    self._check_node(node.body, func_node)
                if hasattr(node, "orelse"):
                    self._check_node(node.orelse, func_node)
            elif isinstance(node, astroid.TryExcept):
                # BUG: astroid.TryExcept doesn't exist in astroid 3.0+
                # Should be astroid.Try
                if hasattr(node, "body"):
                    self._check_node(node.body, func_node)
                if hasattr(node, "handlers"):
                    for handler in node.handlers:
                        if hasattr(handler, "body"):
                            self._check_node(handler.body, func_node)
                if hasattr(node, "orelse"):
                    self._check_node(node.orelse, func_node)
    
    def _check_blocking_call(self, node: astroid.Call, func_node):
        """Check if a call is blocking I/O."""
        # Check direct function names (e.g., open())
        if isinstance(node.func, astroid.Name):
            # BUG: Doesn't resolve import aliases
            # e.g., "from time import sleep as s" -> s() won't be detected
            if node.func.name in self.blocking_functions:
                self.add_message(
                    "blocking-io-in-async",
                    node=node,
                    args=(node.func.name,),
                )
        
        # Check attribute calls (e.g., time.sleep(), requests.get())
        elif isinstance(node.func, astroid.Attribute):
            try:
                qualified_name = self._get_qualified_name(node.func)
                # BUG: Doesn't handle import aliases
                # e.g., "import requests as r" -> r.get() won't match "requests.get"
                if qualified_name in self.blocking_functions:
                    self.add_message(
                        "blocking-io-in-async",
                        node=node,
                        args=(qualified_name,),
                    )
            except Exception:
                pass
    
    def _get_qualified_name(self, node):
        """Get the qualified name of an attribute node."""
        parts = []
        current = node
        while isinstance(current, astroid.Attribute):
            parts.append(current.attrname)
            current = current.expr
        if isinstance(current, astroid.Name):
            parts.append(current.name)
        return ".".join(reversed(parts))

# BUG: Missing register() function required for --load-plugins
