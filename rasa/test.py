import logging
from typing import Text, Dict
import os

from rasa.constants import DEFAULT_RESULTS_PATH
from rasa.model import get_model
from rasa.cli.utils import minimal_kwargs

logger = logging.getLogger(__name__)


def test(model: Text, stories: Text, nlu_data: Text, endpoints: Text = None,
         output: Text = DEFAULT_RESULTS_PATH, **kwargs):
    test_core(model, stories, endpoints, output, **kwargs)
    test_nlu(model, nlu_data, **kwargs)


def test_core(model: Text, stories: Text, endpoints: Text = None,
              output: Text = DEFAULT_RESULTS_PATH, model_path: Text = None,
              **kwargs: Dict):
    import rasa_core.test
    import rasa_core.utils as core_utils
    from rasa_nlu import utils as nlu_utils
    from rasa.model import get_model
    from rasa_core.interpreter import NaturalLanguageInterpreter
    from rasa_core.agent import Agent

    _endpoints = core_utils.AvailableEndpoints.read_endpoints(endpoints)

    if output:
        nlu_utils.create_dir(output)

    if os.path.isfile(model):
        model_path = get_model(model)

    if model_path:
        # Single model: Normal evaluation
        model_path = get_model(model)
        core_path = os.path.join(model_path, "core")
        nlu_path = os.path.join(model_path, "nlu")

        _interpreter = NaturalLanguageInterpreter.create(nlu_path,
                                                         _endpoints.nlu)

        _agent = Agent.load(core_path, interpreter=_interpreter)

        kwargs = minimal_kwargs(kwargs, rasa_core.test)
        rasa_core.test(stories, _agent, out_directory=output, **kwargs)

    else:
        from rasa_core.test import compare, plot_curve

        compare(model, stories, output)

        story_n_path = os.path.join(model, 'num_stories.json')

        number_of_stories = core_utils.read_json_file(story_n_path)
        plot_curve(output, number_of_stories)


def test_nlu(model: Text, nlu_data: Text, **kwargs: Dict):
    from rasa_nlu.test import run_evaluation

    unpacked_model = get_model(model)
    nlu_model = os.path.join(unpacked_model, "nlu")
    kwargs = minimal_kwargs(kwargs, run_evaluation)
    run_evaluation(nlu_data, nlu_model, **kwargs)


def test_nlu_with_cross_validation(config: Text, nlu: Text, folds: int = 3):
    import rasa_nlu.config
    import rasa_nlu.test as nlu_test

    nlu_config = rasa_nlu.config.load(config)
    data = rasa_nlu.training_data.load_data(nlu)
    data = nlu_test.drop_intents_below_freq(data, cutoff=5)
    results, entity_results = nlu_test.cross_validate(data, folds, nlu_config)
    logger.info(f"CV evaluation (n={folds})")

    if any(results):
        logger.info("Intent evaluation results")
        nlu_test.return_results(results.train, "train")
        nlu_test.return_results(results.test, "test")
    if any(entity_results):
        logger.info("Entity evaluation results")
        nlu_test.return_entity_results(entity_results.train, "train")
        nlu_test.return_entity_results(entity_results.test, "test")
