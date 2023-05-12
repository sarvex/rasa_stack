import os
import logging
import shutil
import typing
from typing import Text, Dict, Union, Tuple

from rasa.cli.utils import minimal_kwargs
from rasa.model import get_model, get_model_subdirectories

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from rasa_core.agent import Agent


def run(model: Text, endpoints: Text, connector: Text = None,
        credentials: Text = None, **kwargs: Dict):
    """Runs a Rasa model.

    Args:
        model: Path to model archive.
        endpoints: Path to endpoints file.
        connector: Connector which should be use (overwrites `credentials`
        field).
        credentials: Path to channel credentials file.
        **kwargs: Additional arguments which are passed to
        `rasa_core.run.serve_application`.

    """
    import rasa_core.run

    model_path = get_model(model)
    _agent = create_agent(model_path, endpoints)

    if connector or credentials:
        channel = connector

    else:
        channel = "cmdline"
        logger.info("No chat connector configured, falling back to the "
                    "command line. Use `rasa configure channel` to connect"
                    "the bot to e.g. facebook messenger.")
    kwargs = minimal_kwargs(kwargs, rasa_core.run.serve_application)
    rasa_core.run.serve_application(_agent, channel=channel,
                                    credentials_file=credentials,
                                    **kwargs)
    shutil.rmtree(model_path)


def create_agent(model: Text,
                 endpoints: Text = None) -> 'Agent':
    from rasa_core.broker import PikaProducer
    from rasa_core.interpreter import RasaNLUInterpreter
    import rasa_core.run
    from rasa_core.tracker_store import TrackerStore
    from rasa_core.utils import AvailableEndpoints

    core_path, nlu_path = get_model_subdirectories(model)
    _endpoints = AvailableEndpoints.read_endpoints(endpoints)

    _interpreter = None
    if os.path.exists(nlu_path):
        _interpreter = RasaNLUInterpreter(model_directory=nlu_path)
    else:
        _interpreter = None
        logging.info("No NLU model found. Running without NLU.")

    _broker = PikaProducer.from_endpoint_config(_endpoints.event_broker)

    _tracker_store = TrackerStore.find_tracker_store(None,
                                                     _endpoints.tracker_store,
                                                     _broker)
    return rasa_core.run.load_agent(core_path, interpreter=_interpreter,
                                    tracker_store=_tracker_store,
                                    endpoints=_endpoints)
