from __future__ import annotations

APP_NAME = "Shortcut Studio"
CANVAS = "#0a0a0a"
CARD = "#191919"
SOFT = "#1a1c20"
HAIRLINE = "#2c2f34"
WHITE = "#ffffff"
BODY = "#dadbdf"
MUTED = "#7d8187"
GREEN = "#48d597"
ORANGE = "#ff7a17"
RED = "#ff6b6b"
SURFACE_ELEVATED = "#242424"

STYLESHEET = f"""
* {{
    font-family: "Segoe UI", "Microsoft YaHei UI", "Yu Gothic UI", sans-serif;
    font-size: 14px;
    font-weight: 400;
}}
QMainWindow {{
    background: transparent;
}}
#shell {{
    background: {CANVAS};
    border: 1px solid {HAIRLINE};
    border-radius: 12px;
}}
#shell[maximized="true"] {{
    border: none;
    border-radius: 0px;
}}
#header {{
    background: {CANVAS};
    border-bottom: 1px solid {HAIRLINE};
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}}
#header[maximized="true"] {{
    border-top-left-radius: 0px;
    border-top-right-radius: 0px;
}}
#pages {{
    background: {CANVAS};
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
}}
#pages[maximized="true"] {{
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
}}
QWidget {{
    color: {WHITE};
}}
#brand, #eyebrow {{
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 12px;
    letter-spacing: 2px;
    color: {WHITE};
}}
#monoMuted {{
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 12px;
    letter-spacing: 1px;
    color: {MUTED};
}}
#title {{ font-size: 42px; letter-spacing: -1px; color: {WHITE}; }}
#dashboardTitle {{ font-size: 30px; letter-spacing: -0.6px; color: {WHITE}; }}
#dashboardCardTitle {{ font-size: 18px; color: {WHITE}; }}
#dashboardCardBody {{ font-size: 13px; color: {BODY}; }}
#metric {{ font-size: 28px; color: {WHITE}; }}
#homeRecent {{ font-size: 15px; color: {BODY}; }}
#body {{ font-size: 16px; line-height: 24px; color: {BODY}; }}
QPushButton {{
    background: transparent;
    color: {WHITE};
    border: 1px solid #45484e;
    border-radius: 18px;
    padding: 8px 18px;
    min-height: 18px;
}}
QPushButton:hover {{ border-color: #8b8e94; background: {SOFT}; }}
QPushButton:pressed {{ background: #2a2c31; }}
QPushButton:disabled {{ color: #55585e; border-color: {HAIRLINE}; }}
QPushButton#primaryButton {{ background: {WHITE}; color: {CANVAS}; border-color: {WHITE}; }}
QPushButton#primaryButton:hover {{ background: #e8e8e5; }}
QPushButton#navButton {{
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 16px;
}}
QPushButton#navButton:hover {{ background: {SOFT}; }}
QPushButton#dangerButton {{ color: {RED}; }}

QPushButton#windowControl, QPushButton#windowMinButton, QPushButton#windowMaxButton {{
    background: transparent;
    color: {MUTED};
    border: none;
    border-radius: 6px;
    padding: 0px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#windowControl:hover, QPushButton#windowMinButton:hover, QPushButton#windowMaxButton:hover {{
    background: {SURFACE_ELEVATED};
    color: {WHITE};
}}
QPushButton#windowControl:pressed, QPushButton#windowMinButton:pressed, QPushButton#windowMaxButton:pressed {{
    background: {CARD};
}}
QPushButton#windowCloseControl, QPushButton#windowCloseButton {{
    background: transparent;
    color: {MUTED};
    border: none;
    border-radius: 6px;
    padding: 0px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#windowCloseControl:hover, QPushButton#windowCloseButton:hover {{
    background: #ef4444;
    color: {WHITE};
}}
QPushButton#windowCloseControl:pressed, QPushButton#windowCloseButton:pressed {{
    background: #dc2626;
    color: {WHITE};
}}

QFrame#card, QFrame#folderRow, QFrame#dashboardCard {{
    background: {CARD};
    border: 1px solid {HAIRLINE};
    border-radius: 8px;
}}
QFrame#card QLabel, QFrame#card QCheckBox, QFrame#folderRow QLabel,
QFrame#dashboardCard QLabel {{ background: transparent; }}
QFrame#verticalDivider {{ background: {HAIRLINE}; border: none; }}
QLineEdit {{
    background: {SOFT};
    color: {WHITE};
    border: 1px solid {HAIRLINE};
    border-radius: 8px;
    padding: 11px 14px;
    selection-background-color: #4c4f55;
}}
QLineEdit:focus {{ border-color: #777b82; }}
QProgressBar {{ background: {SOFT}; border: none; border-radius: 3px; height: 6px; }}
QProgressBar::chunk {{ background: {WHITE}; border-radius: 3px; }}
QScrollArea {{ background: transparent; }}
QTreeWidget {{
    background: transparent;
    border: none;
    outline: none;
}}
QTreeWidget::item {{
    background: {CARD};
    border: 1px solid {HAIRLINE};
    padding: 10px 14px;
    color: {BODY};
}}
QTreeWidget::item:hover {{ border-color: #5a5e64; }}
QTreeWidget::item:selected {{ background: {SOFT}; border: 1px solid {WHITE}; color: {WHITE}; }}
QHeaderView::section {{
    background: {CANVAS};
    color: {MUTED};
    border: none;
    border-bottom: 1px solid {HAIRLINE};
    padding: 8px 12px;
    font-family: Consolas, monospace;
    font-size: 11px;
}}
#pairPath, #pairPathMuted {{
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 12px;
}}
#pairPathMuted {{ color: {MUTED}; }}
#itemTitle {{ font-size: 16px; color: {WHITE}; }}
QMessageBox {{ background: {CANVAS}; }}

QMenu {{
    background-color: {CARD};
    border: 1px solid {HAIRLINE};
    border-radius: 8px;
    padding: 4px;
    color: {WHITE};
}}
QMenu::item {{
    background: transparent;
    padding: 6px 18px 6px 12px;
    border-radius: 4px;
    color: {BODY};
    font-size: 13px;
}}
QMenu::item:selected {{
    background-color: {SURFACE_ELEVATED};
    color: {WHITE};
}}
QMenu::separator {{
    height: 1px;
    background: {HAIRLINE};
    margin: 4px 6px;
}}
"""
