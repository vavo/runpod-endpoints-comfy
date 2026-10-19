from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from .settings import install_routes
from .catalog_nodes import FormaImage, FormaVideo

NODE_CLASS_MAPPINGS.update({"FormaImage": FormaImage, "FormaVideo": FormaVideo})
NODE_DISPLAY_NAME_MAPPINGS.update({"FormaImage": "Forma · Image (Choose Model)", "FormaVideo": "Forma · Video (Choose Model)"})
from server import PromptServer

WEB_DIRECTORY = "./web"
install_routes(PromptServer.instance.routes)

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
