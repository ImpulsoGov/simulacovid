# coding=utf-8
import streamlit as st
import yaml
import os

# Environment Variables from '../.env'
from dotenv import load_dotenv
from pathlib import Path

env_path = Path("..") / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Pages
import pages.team as tm

# import pages.model_description as md
# import pages.saude_em_ordem_description as sod
import pages.main as fc
import pages.methodology as method

import utils

# Packages
from streamlit import caching
import session
import time


def main():

    # SESSION STATE
    time.sleep(
        0.05
    )  # minimal wait time so we give time for the user session to appear in steamlit
    session_state = session.SessionState.get(
        key=session.get_user_id(),
        update=False,
        state_name="Acre",
        state_num_id=None,
        health_region_name="Todos",
        health_region_id=None,
        city_name="Todos",
        city_id=None,
        number_beds=None,
        number_icu_beds=None,
        number_cases=None,
        number_deaths=None,
        population_params=dict(),
        refresh=False,
        reset=False,
        saude_ordem_data=None,
        already_generated_user_id=None,
        pages_open=None,
        amplitude_events=None,
        old_amplitude_events=None,
        button_styles=dict(),
        continuation_selection=None,
    )
    # AMPLITUDE EVENT
    # In those amplitude events objects we are going to save a dict with every state as keys
    # in each state, the value will be something that allows us to identify there is a change or not
    # which in turn allows us to decide if we should log the event or not
    if os.getenv("IS_DEV").upper() == "FALSE":
        utils.manage_user_existence(utils.get_server_session(), session_state)
        utils.update_user_public_info()

    # CLOSES THE SIDEBAR WHEN THE USER LOADS THE PAGE
    st.write(
        """
    <iframe src="resources/sidebar-closer.html" height=0 width=0>
    </iframe>""",
        unsafe_allow_html=True,
    )
    # For Http debug
    # st.write(utils.parse_headers(utils.get_server_session().ws.request))

    # MENU
    page = st.sidebar.radio(
        "Menu", ["FarolCovid", "Modelos, limitações e fontes", "Quem somos?",],
    )

    if page == "FarolCovid":
        if __name__ == "__main__":
            fc.main(session_state)
            utils.applyButtonStyles(session_state)

    elif page == "Quem somos?":
        if __name__ == "__main__":
            tm.main(session_state)

    elif page == "Modelos, limitações e fontes":
        if __name__ == "__main__":
            method.main(session_state)


if __name__ == "__main__":
    main()
