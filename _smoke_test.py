"""Quick smoke test: build the Gradio UI without launching a server."""
import sys
sys.path.insert(0, ".")

from config import ensure_data_dirs
from repositories.database import initialize_db
ensure_data_dirs()
initialize_db()

from unittest.mock import MagicMock
from repositories.prompt_repository import PromptRepository
from storage.prompt_storage import PromptStorage
from agents.prompt_generator_agent import PromptGeneratorAgent
from agents.prompt_optimizer_agent import PromptOptimizerAgent
from services.prompt_service import PromptService
from services.optimization_service import OptimizationService
from ui.main import create_ui
import gradio as gr

ps = PromptService.__new__(PromptService)
mock = MagicMock()
ps._repo      = PromptRepository()
ps._storage   = PromptStorage()
ps._client    = mock
ps._generator = PromptGeneratorAgent(mock)
ps._optimizer = PromptOptimizerAgent(mock)
os_svc = OptimizationService(ps)

app = create_ui(ps, os_svc)
print(f"UI built successfully — Gradio {gr.__version__}")
