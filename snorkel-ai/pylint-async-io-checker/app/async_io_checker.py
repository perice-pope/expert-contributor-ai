# CANARY_STRING_PLACEHOLDER
"""Pylint plugin to detect blocking I/O in async functions."""
import astroid
from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker
from pylint.lint import PyLinter


class AsyncIOChecker(BaseChecker):
    """Checker for blocking I/O operations in async functions."""
    
    __implements__ = IAstroidChecker
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
        # BUG: Default blocking functions list is incomplete
        self.blocking_functions = ["open", "time.sleep"]
        self.enabled = True
        # BUG: Doesn't read configuration from pyproject.toml
    
    def visit_functiondef(self, node: astroid.FunctionDef):
        """Visit function definitions."""
        if not self.enabled:
            return
        
        # BUG: Only checks for 'async def', misses @asyncio.coroutine decorator
        if not node.is_async:
            return
        
        # BUG: Doesn't traverse nested function calls properly
        # BUG: Only checks top-level calls, misses calls inside if/for/while blocks
        for child in node.body:
            if isinstance(child, astroid.Call):
                self._check_blocking_call(child, node)
    
    def visit_asyncfunctiondef(self, node: astroid.AsyncFunctionDef):
        """Visit async function definitions."""
        # BUG: This method exists but visit_functiondef should handle async functions too
        # This creates duplicate checking logic
        self.visit_functiondef(node)
    
    def _check_blocking_call(self, node: astroid.Call, func_node):
        """Check if a call is blocking I/O."""
        # BUG: Only checks direct function names, doesn't handle attribute calls like time.sleep()
        # BUG: Doesn't check for requests.get(), requests.post(), urllib.request.urlopen(), etc.
        if isinstance(node.func, astroid.Name):
            if node.func.name in self.blocking_functions:
                self.add_message(
                    "blocking-io-in-async",
                    node=node,
                    args=(node.func.name,),
                )
        # BUG: Missing handling for astroid.Attribute nodes (e.g., time.sleep, requests.get)
