from .auth import router as auth_router
from .scans import router as scans_router
from .questionnaire import router as questionnaire_router
from .derm_locator import router as derm_locator_router

__all__ = [
    "auth_router",
    "scans_router",
    "questionnaire_router",
    "derm_locator_router",
]
