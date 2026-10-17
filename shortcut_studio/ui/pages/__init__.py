from __future__ import annotations

from shortcut_studio.ui.pages.check_page import build_check_page
from shortcut_studio.ui.pages.choice_page import build_choice_page
from shortcut_studio.ui.pages.done_page import build_done_page
from shortcut_studio.ui.pages.edit_detail_page import build_edit_detail_page
from shortcut_studio.ui.pages.edit_page import build_edit_page
from shortcut_studio.ui.pages.home_page import build_home_page
from shortcut_studio.ui.pages.list_page import build_list_page
from shortcut_studio.ui.pages.progress_page import build_progress_page
from shortcut_studio.ui.pages.settings_page import build_settings_page
from shortcut_studio.ui.pages.setup_page import build_setup_page

__all__ = [
    "build_home_page",
    "build_setup_page",
    "build_check_page",
    "build_list_page",
    "build_edit_page",
    "build_edit_detail_page",
    "build_settings_page",
    "build_progress_page",
    "build_choice_page",
    "build_done_page",
]
