import os
import sys
import gettext
import builtins
from pathlib import Path
from typing import Callable


def init_gettext(locale_dir: str | Path, locale_name: str) -> Callable[[str], str]:
    mo_path = Path(locale_dir) / locale_name / 'LC_MESSAGES' / f'{locale_name}.mo'
    if not mo_path.exists():
        raise FileNotFoundError(f"Translation file not found: {mo_path}")

    translation = gettext.translation(
        locale_name,
        localedir=str(locale_dir),
        languages=[locale_name],
        fallback=False
    )
    return translation.gettext


execute_dir = os.path.split(os.path.realpath(sys.argv[0]))[0]
if os.path.exists(Path(execute_dir) / '_internal/i18n'):
    locale_path = Path(execute_dir) / '_internal/i18n'
else:
    locale_path = Path(execute_dir) / 'i18n'

_tr: Callable[[str], str] = lambda x: x
_translation_available: bool = False

try:
    _tr = init_gettext(locale_path, 'zh_CN')
    _translation_available = True
except FileNotFoundError:
    _translation_available = False
except Exception as e:
    _translation_available = False
    try:
        from src.logger import logger
        logger.warning(f"i18n initialization failed: {e}")
    except ImportError:
        pass

original_print = builtins.print
_package_prefix = os.sep + 'src' + os.sep


def translated_print(*args, **kwargs) -> None:
    try:
        caller_file = sys._getframe(1).f_code.co_filename
        should_translate = _package_prefix in caller_file and _translation_available
    except (ValueError, AttributeError):
        should_translate = False

    sep = kwargs.get('sep', ' ')
    translated_args = []
    for arg in args:
        text = str(arg)
        if should_translate:
            try:
                text = _tr(text)
            except Exception:
                pass
        translated_args.append(text)

    original_print(sep.join(translated_args), **kwargs)
