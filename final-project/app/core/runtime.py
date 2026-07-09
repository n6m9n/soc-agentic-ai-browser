"""Process-wide singletons shared across routers (avoids circular imports)."""
from app.core.hub import TaskHub

hub = TaskHub()
