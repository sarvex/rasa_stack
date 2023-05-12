import os
import tempfile
import typing
from typing import Text, Optional, List, Union

from rasa import model, data
from rasa.cli.utils import create_output_path
from rasa.constants import DEFAULT_MODELS_PATH

if typing.TYPE_CHECKING:
    from rasa_nlu.model import Interpreter


def train(domain: Text, config: Text, training_files: Union[Text, List[Text]],
          output: Text = DEFAULT_MODELS_PATH, force_training: bool = False
          ) -> Optional[Text]:
    """Trains a Rasa model (Core and NLU).

    Args:
        domain: Path to the domain file.
        config: Path to the config for Core and NLU.
        training_files: Paths to the training data for Core and NLU.
        output: Output path.
        force_training: If `True` retrain model even if data has not changed.

    Returns:
        Path of the trained model archive.
    """
    from rasa_core.utils import print_success

    train_path = tempfile.mkdtemp()
    old_model = model.get_latest_model(output)
    retrain_core = True
    retrain_nlu = True

    story_directory, nlu_data_directory = data.get_core_nlu_directories(
        training_files)
    new_fingerprint = model.model_fingerprint(config, domain,
                                              nlu_data_directory,
                                              story_directory)
    if not force_training and old_model:
        unpacked = model.unpack_model(old_model)
        old_core, old_nlu = model.get_model_subdirectories(unpacked)
        last_fingerprint = model.fingerprint_from_path(unpacked)

        if not model.core_fingerprint_changed(last_fingerprint,
                                              new_fingerprint):
            target_path = os.path.join(train_path, "core")
            retrain_core = not model.merge_model(old_core, target_path)

        if not model.nlu_fingerprint_changed(last_fingerprint, new_fingerprint):
            target_path = os.path.join(train_path, "nlu")
            retrain_nlu = not model.merge_model(old_nlu, target_path)

    if force_training or retrain_core:
        train_core(domain, config, story_directory, output, train_path)
    else:
        print("Core configuration did not change. No need to retrain "
              "Core model.")

    if force_training or retrain_nlu:
        train_nlu(config, nlu_data_directory, output, train_path)
    else:
        print("NLU configuration did not change. No need to retrain NLU model.")

    if retrain_core or retrain_nlu:
        output = create_output_path(output)
        model.create_package_rasa(train_path, output, new_fingerprint)

        print(f"Train path: '{train_path}'.")

        print_success("Your bot is trained and ready to take for a spin!")

        return output
    else:
        print(f"Nothing changed. You can use the old model: '{old_model}'.")

        return old_model


def train_core(domain: Text, config: Text, stories: Text, output: Text,
               train_path: Optional[Text]) -> Optional[Text]:
    """Trains a Core model.

    Args:
        domain: Path to the domain file.
        config: Path to the config file for Core.
        stories: Path to the Core training data.
        output: Output path.
        train_path: If `None` the model will be trained in a temporary
            directory, otherwise in the provided directory.

    Returns:
        If `train_path` is given it returns the path to the model archive,
        otherwise the path to the directory with the trained model files.

    """
    import rasa_core.train
    from rasa_core.utils import print_success

    # normal (not compare) training
    core_model = rasa_core.train(domain_file=domain, stories_file=stories,
                                 output_path=os.path.join(train_path, "core"),
                                 policy_config=config)

    if not train_path:
        # Only Core was trained.
        stories = data.get_core_directory(stories)
        output_path = create_output_path(output, prefix="core-")
        new_fingerprint = model.model_fingerprint(config, domain,
                                                  stories=stories)
        model.create_package_rasa(train_path, output_path, new_fingerprint)
        print_success(f"Your Rasa Core model is trained and saved at '{output_path}'.")

    return core_model


def train_nlu(config: Text, nlu_data: Text, output: Text,
              train_path: Optional[Text]) -> Optional["Interpreter"]:
    """Trains a NLU model.

    Args:
        config: Path to the config file for NLU.
        nlu_data: Path to the NLU training data.
        output: Output path.
        train_path: If `None` the model will be trained in a temporary
            directory, otherwise in the provided directory.

    Returns:
        If `train_path` is given it returns the path to the model archive,
        otherwise the path to the directory with the trained model files.

    """
    import rasa_nlu
    from rasa_core.utils import print_success

    _train_path = train_path or tempfile.mkdtemp()
    _, nlu_model, _ = rasa_nlu.train(config, nlu_data, _train_path,
                                     project="",
                                     fixed_model_name="nlu")

    if not train_path:
        nlu_data = data.get_nlu_directory(nlu_data)
        output_path = create_output_path(output, prefix="nlu-")
        new_fingerprint = model.model_fingerprint(config, nlu_data=nlu_data)
        model.create_package_rasa(_train_path, output_path, new_fingerprint)
        print_success(f"Your Rasa NLU model is trained and saved at '{output_path}'.")

    return nlu_model
