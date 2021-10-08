import re
import subprocess

from src.goodies import print_warning


OS = {
    "macOS": {
        "QUERY_DEFAULTS_COMMAND": [
            "defaults",
            "read",
            "com.apple.LaunchServices/com.apple.launchservices.secure",
            "LSHandlers",
        ],
        "REGEX": r'(?ms)\s*\{\s*LSHandlerContentType = "public\.plain-text";\s*LSHandlerPreferredVersions =\s*\{\s*LSHandlerRoleAll = "-";\s*\};\s*LSHandlerRoleAll = "([\w.]+)";',
        "DEFAULT_COMMAND": [
            "open",
            "-neW",
        ],
        "EDITOR_COMMAND": {
            "com.microsoft.vscode": ["code", "-w"],
            "com.sublimetext.3": ["subl", "-w"],
        },  # TODO: add different versions of Sublime Text
    },
    "Linux": {
        "QUERY_DEFAULTS_COMMAND": [
            "xdg-mime",
            "query",
            "default",
            "text/plain",
        ],
        "REGEX": r"^(.*)\.desktop$",
        "DEFAULT_COMMAND": ["open", "-w"],
        "EDITOR_COMMAND": {
            "code": ["code", "-w"],
            "sublime_text": ["subl", "-w"],
        },
    },
}


def get_editor_command_name(os_name: str = "") -> list:
    """
    Retrieve the system's default text editor.

    Args:
        os_name: operating system's name
            macOS and Linux (with XDG utils installed) currently supported

    Returns:
        The default text editor's command name for supported editors.
        The `open -w` command for an unsupported or undefined editor.

    Raises:
        UnsupportedOS Error if the os is not supported.
    """
    os = OS.get(os_name)
    if not os:
        raise UnsupportedOS("OS not yet supported.")
    parse_output = re.compile(str(os["REGEX"])).findall  # make mypy happy
    try:
        result = parse_output(
            subprocess.run(
                list(os["QUERY_DEFAULTS_COMMAND"]),  # make mypy happy
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            ).stdout
        )
        if result:
            return os["EDITOR_COMMAND"][result[0]]  # type: ignore
    except (subprocess.CalledProcessError, KeyError) as e:
        print_warning(str(e))  # make mypy happy
    return list(os["DEFAULT_COMMAND"])  # make mypy happy


class UnsupportedOS(Exception):
    ...
