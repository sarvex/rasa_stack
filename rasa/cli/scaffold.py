import os
import argparse
from typing import List, Text

import questionary
import rasa.train
from rasa.cli.shell import shell
from rasa.cli.utils import create_output_path
from rasa_core.utils import print_success

from rasa.constants import (DEFAULT_CONFIG_PATH, DEFAULT_DOMAIN_PATH,
                            DEFAULT_DATA_PATH)


def add_subparser(subparsers: argparse._SubParsersAction,
                  parents: List[argparse.ArgumentParser]):
    scaffold_parser = subparsers.add_parser(
        "init",
        parents=parents,
        help="Create a new project from a initial_project")
    scaffold_parser.set_defaults(func=run)


def print_train_or_instructions(args: argparse.Namespace, path: Text) -> None:
    print_success("Your bot is ready to go!")
    if should_train := questionary.confirm(
        "Do you want me to train an initial " "model for the bot? 💪🏽"
    ).ask():
        config = os.path.join(path, DEFAULT_CONFIG_PATH)
        training_files = os.path.join(path, DEFAULT_DATA_PATH)
        domain = os.path.join(path, DEFAULT_DOMAIN_PATH)
        output = os.path.join(path, create_output_path())

        args.model = rasa.train(domain, config, training_files, output)

        print_run_or_instructions(args, path)

    else:
        print_success("No problem 👍🏼. You can also train me later by going "
                      "to the project directory and running 'rasa train'."
                      "".format(path))


def print_run_or_instructions(args: argparse.Namespace, path: Text) -> None:
    from rasa_core import constants

    if should_run := questionary.confirm(
        "Do you want to speak to the trained bot " "on the command line? 🤖"
    ).ask():
        # provide defaults for command line arguments
        attributes = ["endpoints", "credentials", "cors", "auth_token",
                      "jwt_secret", "jwt_method", "enable_api"]
        for a in attributes:
            setattr(args, a, None)

        args.port = constants.DEFAULT_SERVER_PORT

        shell(args)
    else:
        print_success("Ok 👍🏼. If you want to speak to the bot later, "
                      "change into the project directory and run 'rasa shell'."
                      "".format(path))


def init_project(args: argparse.Namespace, path: Text) -> None:
    _create_initial_project(path)
    print(f"Created project directory at '{os.path.abspath(path)}'.")
    print_train_or_instructions(args, path)


def _create_initial_project(path: Text) -> None:
    from distutils.dir_util import copy_tree

    copy_tree(scaffold_path(), path)


def scaffold_path() -> Text:
    import pkg_resources
    return pkg_resources.resource_filename(__name__, "initial_project")


def print_cancel() -> None:
    print_success("Ok. Then I stop here. If you need me again, simply type "
                  "'rasa init' 🙋🏽‍♀️")
    exit(0)


def _ask_create_path(path: Text) -> None:
    if should_create := questionary.confirm(
        f"Path '{path}' does not exist 🧐. Should I create it?"
    ).ask():
        os.makedirs(path)
    else:
        print_success("Ok. Then I stop here. If you need me again, simply type "
                      "'rasa init' 🙋🏽‍♀️")
        exit(0)


def _ask_overwrite(path: Text) -> None:
    overwrite = questionary.confirm(
        f"Directory '{os.path.abspath(path)}' is not empty. Continue?"
    ).ask()
    if not overwrite:
        print_cancel()


def run(args: argparse.Namespace) -> None:
    from rasa_core.utils import print_success

    print_success("Welcome to Rasa! 🤖\n")
    print("To get started quickly, I can assist you to create an "
          "initial project.\n"
          "If you need some help to get from this template to a "
          "bad ass contextual assistant, checkout our quickstart guide"
          "here: https://rasa.com/docs/core/quickstart \n\n"
          "Now let's start! 👇🏽\n")
    path = questionary.text("Please enter a folder path where I should create "
                            "the initial project [default: current directory]",
                            default=".").ask()

    if not os.path.isdir(path):
        _ask_create_path(path)

    if path is None or not os.path.isdir(path):
        print_cancel()

    if len(os.listdir(path)) > 0:
        _ask_overwrite(path)

    init_project(args, path)
