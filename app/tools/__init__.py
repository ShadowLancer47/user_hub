from fastapi import APIRouter

class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, tool_name: str, router: APIRouter):
        self.tools[tool_name] = router

registry = ToolRegistry()
