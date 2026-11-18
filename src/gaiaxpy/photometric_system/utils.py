"""Provide loading prompts and built-in system-name and column-label helpers."""
from importlib.resources import files
from string import capwords

from gaiaxpy.core.generic_variables import RELEASES


def execute_answer(action, message=None, args=None):
    """Run an optional callback, then print its optional completion message.

    Args:
        action (callable or None): Callback to run. A false value does nothing.
        message (str or None): Message printed only after an action runs.
        args (object or None): If truthy, pass this object as one positional
            argument; otherwise call the action without arguments.

    Notes:
        The callback's return value is discarded; arguments are not unpacked.
    """
    if action:
        if args:
            action(args)
        else:
            action()
        if message:
            print(message)


def get_yes_no_answer(question, yes_action, no_action, yes_message=None, no_message=None, yes_args=None, no_args=None):
    """Prompt until a yes/no answer is given, then run the chosen callback.

    Args:
        question (str): Prompt displayed by input(). An empty answer selects yes.
        yes_action (callable or None): Callback for y or yes, ignoring case.
        no_action (callable or None): Callback for n or no, ignoring case.
        yes_message (str or None): Completion message after a yes action runs.
        no_message (str or None): Completion message after a no action runs.
        yes_args (object or None): Optional single argument for yes_action.
        no_args (object or None): Optional single argument for no_action.

    Notes:
        Invalid answers repeat the prompt. Callback arguments and messages are
        handled by execute_answer; callback return values are discarded.
    """
    default = 'y'
    yes_choices = ['yes', default]
    no_choices = ['no', 'n']
    while True:
        user_input = input(question) or default
        if user_input.lower() in yes_choices:
            execute_answer(yes_action, yes_message, yes_args)
            break
        elif user_input.lower() in no_choices:
            execute_answer(no_action, no_message, no_args)
            break
        else:
            print('Please type yes or no.')
            continue


def _get_built_in_systems_base_names(release=None) -> list:
    """Read non-empty base names from the release's bundled available-systems file.

    Args:
        release (str): Release label such as 'dr3', ignoring case.
            A string is required despite the None default.

    Returns:
        list[str]: Names in file order, without release prefixes.
    """
    resource = files('gaiaxpy.config').joinpath(f'{release.lower()}_available_systems.txt')
    with resource.open(encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def _is_dr3_builtin_system(system):
    """Return whether the exact base name appears in the bundled DR3 list."""
    return system in _get_built_in_systems_base_names(release=RELEASES.dr3)


def _get_system_label(name):
    """Build a photometry column label from a base system name.

    Known built-in names have underscores removed and words capitalised using
    the existing label convention. Other names retain their spelling. Additional
    filter version suffixes are added separately.
    """

    def snake_to_pascal(word):
        """Replace underscores with word boundaries and join capitalised words."""
        return capwords(word.replace("_", " ")).replace(" ", "")

    return snake_to_pascal(name) if _is_dr3_builtin_system(name) else name
