import app_paths

app_paths.ensure_runtime_cwd()

from utils.win_icon import apply_app_icon

apply_app_icon()

import config
from remote_client import RemoteClient


if __name__ == "__main__":
    name = config.get_client_name()
    port = config.get_port()
    server_url = config.get_server_url()
    debug = bool(config.get_setting("debug", False))

    config.logger.info(
        f"Starting Remote Task Manager Client name={name} port={port} server={server_url}"
    )
    client = RemoteClient(name=name, port=port, target_url=server_url, debug=debug)
    client.start_server()
