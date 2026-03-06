# -*- coding: utf-8 -*-
"""CSS styles and backend activity chip for the file panel UI."""

from __future__ import annotations

import streamlit as st

from ui.i18n import t

_FILE_PANEL_CSS = """
        <style>
        :root {
            --main-top-offset: 3.55rem;
            --settings-panel-edge: 20.2rem;
            --files-panel-width: 26.35rem;
            --files-panel-gap: 18.9px; /* 5 mm ~= 18.9 px ~= 14.17 pt */
            --files-panel-reserve-extra: 1.2rem;
            --files-list-fixed-height: 28rem;
        }
        body:has(section[data-testid="stSidebar"][aria-expanded="false"]) {
            --settings-panel-edge: 3.35rem;
        }
        [data-testid="stSidebarUserContent"] {
            padding-top: 0.05rem;
        }
        div.st-key-lang_picker {
            margin-top: -1.0rem;
            margin-bottom: 0.2rem;
            max-width: 34%;
        }
        div.st-key-lang_picker p {
            margin-bottom: 0.2rem;
        }
        div.st-key-lang_picker [data-baseweb="select"] {
            cursor: pointer !important;
        }
        div.st-key-lang_picker [data-baseweb="select"] * {
            cursor: pointer !important;
        }
        .lang-flag-row {
            display: flex;
            gap: 0.7rem;
            align-items: center;
            margin-bottom: 0.25rem;
            font-size: 0.82rem;
            opacity: 0.95;
        }
        .lang-flag-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.32rem;
        }
        .lang-flag-chip svg {
            width: 14px;
            height: 10px;
            border-radius: 1px;
            box-shadow: 0 0 0 1px rgba(255,255,255,0.15);
        }
        div.st-key-pii_mark_safe button {
            background: #1f9d55 !important;
            border-color: #1f9d55 !important;
            color: #ffffff !important;
            font-weight: 700;
        }
        div.st-key-pii_mark_safe button:hover {
            background: #1b8748 !important;
            border-color: #1b8748 !important;
        }
        [data-testid="stAppViewContainer"] [data-testid="stMain"] .block-container {
            max-width: none;
            padding-left: 0;
            padding-right: 0.7rem;
            padding-top: 0 !important;
        }
        div.st-key-workspace_layout {
            margin-top: 2px;
            margin-left: 2px;
        }
        div.st-key-workspace_layout > div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] {
            align-items: flex-start;
            flex-wrap: nowrap !important;
        }
        div.st-key-workspace_layout > div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child,
        div.st-key-workspace_layout > div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child {
            flex: 0 0 calc(var(--files-panel-width) + var(--files-panel-gap) + var(--files-panel-reserve-extra)) !important;
            max-width: calc(var(--files-panel-width) + var(--files-panel-gap) + var(--files-panel-reserve-extra)) !important;
            min-width: calc(var(--files-panel-width) + var(--files-panel-gap) + var(--files-panel-reserve-extra)) !important;
        }
        div.st-key-workspace_layout > div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2),
        div.st-key-workspace_layout > div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(2) {
            flex: 1 1 auto;
            min-width: 0 !important;
        }
        div.st-key-exit_app_action {
            position: fixed;
            top: 4.25rem;
            right: 3.2rem;
            z-index: 1100;
        }
        div.st-key-exit_app_action button {
            background: #ffffff !important;
            color: #cf1f1f !important;
            font-size: 14px !important;
            font-weight: 800 !important;
            border: 1px solid #ffffff !important;
            border-radius: 10px !important;
            padding: 0.4rem 0.85rem !important;
            min-height: 2.1rem !important;
            line-height: 1.2 !important;
            white-space: nowrap !important;
            width: max-content !important;
        }
        div.st-key-exit_app_action button p,
        div.st-key-exit_app_action button span {
            color: #cf1f1f !important;
            font-size: 14px !important;
            font-weight: 800 !important;
        }
        div.st-key-exit_app_action button:hover {
            background: #f4f4f4 !important;
            border-color: #f4f4f4 !important;
        }
        div.st-key-file_panel_shell {
            background: #171f2d;
            border: 1px solid #2f3a4f;
            border-radius: 12px;
            padding: 0.85rem 0.95rem 0.9rem;
            box-sizing: border-box;
            position: fixed !important;
            left: calc(var(--settings-panel-edge) + var(--files-panel-gap)) !important;
            top: calc(var(--main-top-offset) + 2px) !important;
            width: var(--files-panel-width) !important;
            max-width: var(--files-panel-width) !important;
            min-width: 0 !important;
            margin-left: 0 !important;
            height: calc(100vh - var(--main-top-offset) - 4px);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
            z-index: 970;
        }
        div.st-key-file_panel_filter_wrap {
            background: #101827;
            border: 1px solid #2c3a50;
            border-radius: 10px;
            padding: 0.65rem;
            flex: 1 1 auto;
            min-height: 0;
            overflow-y: auto;
            overflow-x: hidden;
            order: 2;
        }
        div.st-key-file_list_scroll {
            background: #131a27;
            border: 1px solid #314057;
            border-radius: 10px;
            padding: 0.55rem;
            height: var(--files-list-fixed-height);
            min-height: var(--files-list-fixed-height);
            max-height: var(--files-list-fixed-height);
            flex: 0 0 var(--files-list-fixed-height);
            overflow-y: auto;
            order: 1;
        }
        div.st-key-file_list_scroll [data-testid="stVerticalBlockBorderWrapper"] {
            border: none !important;
        }
        #backend-activity-chip {
            position: fixed;
            top: 4.25rem;
            right: 13rem;
            z-index: 1090;
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
            background: rgba(23, 31, 45, 0.93);
            border: 1px solid #2f3a4f;
            border-radius: 999px;
            padding: 0.36rem 0.68rem;
            color: #d9e4ff;
            font-size: 0.84rem;
            font-weight: 600;
            backdrop-filter: blur(5px);
        }
        #backend-activity-chip .state-busy {
            display: none;
            color: #ffdca8;
        }
        #backend-activity-chip .backend-icon {
            position: relative;
            width: 0.95rem;
            height: 0.95rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: #76c5ff;
        }
        #backend-activity-chip .pulse-core,
        #backend-activity-chip .pulse-ring,
        #backend-activity-chip .orbit-ring,
        #backend-activity-chip .orbit-dot,
        #backend-activity-chip .bars {
            display: none;
        }
        #backend-activity-chip.pulse .pulse-core {
            display: block;
            width: 0.42rem;
            height: 0.42rem;
            border-radius: 50%;
            background: currentColor;
        }
        #backend-activity-chip.pulse .pulse-ring {
            display: block;
            position: absolute;
            inset: -0.1rem;
            border: 1px solid currentColor;
            border-radius: 50%;
            opacity: 0.25;
            animation: de-pulse 1.4s ease-out infinite;
        }
        #backend-activity-chip.orbit .orbit-ring {
            display: block;
            width: 0.85rem;
            height: 0.85rem;
            border: 1px solid rgba(118, 197, 255, 0.45);
            border-radius: 50%;
        }
        #backend-activity-chip.orbit .orbit-dot {
            display: block;
            position: absolute;
            width: 0.22rem;
            height: 0.22rem;
            border-radius: 50%;
            background: currentColor;
            top: 0.02rem;
            left: 50%;
            transform-origin: 0 0.45rem;
            animation: de-orbit 1.2s linear infinite;
        }
        #backend-activity-chip.bars .bars {
            display: inline-flex;
            gap: 0.1rem;
            align-items: flex-end;
            height: 0.76rem;
        }
        #backend-activity-chip.bars .bars span {
            width: 0.16rem;
            border-radius: 1px;
            background: currentColor;
            animation: de-bars 1s ease-in-out infinite;
        }
        #backend-activity-chip.bars .bars span:nth-child(1) {
            height: 0.34rem;
            animation-delay: 0s;
        }
        #backend-activity-chip.bars .bars span:nth-child(2) {
            height: 0.7rem;
            animation-delay: 0.16s;
        }
        #backend-activity-chip.bars .bars span:nth-child(3) {
            height: 0.48rem;
            animation-delay: 0.28s;
        }
        #backend-busy-overlay {
            position: fixed;
            inset: 0;
            z-index: 980;
            background: rgba(2, 6, 23, 0.36);
            opacity: 0;
            pointer-events: none;
            transition: opacity 150ms ease;
        }
        body:has(div[data-testid="stSpinner"]) #backend-busy-overlay {
            opacity: 1;
            pointer-events: auto;
        }
        body:has(div[data-testid="stSpinner"]) #backend-activity-chip {
            color: #ffdca8;
            border-color: #775b2f;
            background: rgba(50, 34, 12, 0.9);
        }
        body:has(div[data-testid="stSpinner"]) #backend-activity-chip .state-idle {
            display: none;
        }
        body:has(div[data-testid="stSpinner"]) #backend-activity-chip .state-busy {
            display: inline;
        }
        @keyframes de-pulse {
            0% { transform: scale(0.8); opacity: 0.8; }
            100% { transform: scale(1.45); opacity: 0; }
        }
        @keyframes de-orbit {
            from { transform: rotate(0deg) translateY(0.38rem); }
            to { transform: rotate(360deg) translateY(0.38rem); }
        }
        @keyframes de-bars {
            0%, 100% { transform: scaleY(0.55); opacity: 0.7; }
            50% { transform: scaleY(1.1); opacity: 1; }
        }
        </style>
"""


def render_styles() -> None:
    st.markdown(_FILE_PANEL_CSS, unsafe_allow_html=True)


def render_backend_chip(style: str) -> None:
    chip_style = style if style in {"pulse", "orbit", "bars"} else "pulse"
    st.markdown(
        f"""
        <div id="backend-busy-overlay" aria-hidden="true"></div>
        <div id="backend-activity-chip" class="{chip_style}" aria-live="polite">
          <span class="backend-icon" aria-hidden="true">
            <span class="pulse-core"></span>
            <span class="pulse-ring"></span>
            <span class="orbit-ring"></span>
            <span class="orbit-dot"></span>
            <span class="bars"><span></span><span></span><span></span></span>
          </span>
          <span class="state-idle">{t("backend_status_idle")}</span>
          <span class="state-busy">{t("backend_status_busy")}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
