import os
import sys

sys.path.insert(0, "./model/")

import streamlit as st
from streamlit import caching
from models import (
    BackgroundColor,
    Document,
    Strategies,
    SimulatorOutput,
    ResourceAvailability,
)
from typing import List
import utils
import amplitude
import plotly.express as px
from datetime import datetime
import math
import yaml
import numpy as np
import loader
from model import simulator
from plots import plot_simulation
from pandas import Timestamp
import session


# CAPACITY
def _calculate_recovered(df, params):

    confirmed_adjusted = int(
        df[["confirmed_cases"]].sum() / df["notification_rate"].values[0]
    )

    if confirmed_adjusted == 0:  # dont have any cases yet
        params["population_params"]["R"] = 0
        return params

    params["population_params"]["R"] = (
        confirmed_adjusted
        - params["population_params"]["I"]
        - params["population_params"]["D"]
    )

    if params["population_params"]["R"] < 0:
        params["population_params"]["R"] = (
            confirmed_adjusted - params["population_params"]["D"]
        )

    return params


def _prepare_simulation(user_input, config):

    # based on Alison Hill: 40% asymptomatic
    user_input["population_params"]["I"] = [
        int(
            user_input["population_params"]["I"]
            * (1 - config["br"]["seir_parameters"]["asymptomatic_proportion"])
        )
        if not np.isnan(user_input["population_params"]["I"])
        else 1
    ][0]

    place_specific_params = loader.read_data(
        "br",
        config,
        endpoint=config["br"]["api"]["endpoints"]["parameters"][
            user_input["place_type"]
        ],
    ).set_index(user_input["place_type"])
    place_id = user_input["place_type"]

    user_input["place_specific_params"] = {
        "fatality_ratio": place_specific_params["fatality_ratio"].loc[
            int(user_input[place_id])
        ],
        "i1_percentage": place_specific_params["i1_percentage"].loc[
            int(user_input[place_id])
        ],
        "i2_percentage": place_specific_params["i2_percentage"].loc[
            int(user_input[place_id])
        ],
        "i3_percentage": place_specific_params["i3_percentage"].loc[
            int(user_input[place_id])
        ],
    }
    return user_input


def main(user_input, indicators, data, config, session_state):
    # Amplitude: Get user info
    user_analytics = amplitude.Amplitude_user()
    user_analytics.gen_user(utils.get_server_session())

    utils.localCSS("style.css")

    utils.genHeroSection(
        title1="Simula",
        title2="Covid",
        subtitle="Um simulador da demanda por leitos hospitalares.",
        logo="https://i.imgur.com/w5yVANW.png",
        header=False,
    )

    if (
        user_input["place_type"] == user_input["rt_level"]
    ):  # indicators["rt"].display != "- ":
        st.write(
            f"""
            <div class="base-wrapper">
                    <span class="section-header primary-span">Simule o impacto de diferentes ritmos de contágio no seu sistema hospitalar</span>
                    <br><br>
                    <span>Agora é a hora de se preparar para evitar a sobrecarga hospitalar. 
                    No momento, em {user_input["locality"]}, estimamos que <b>a taxa de contágio esteja entre {indicators["control"].left_display}</b>, 
                    ou seja, cada pessoa doente infectará em média entre outras {indicators["control"].left_display} pessoas.
                    </span>
            </div>""",
            unsafe_allow_html=True,
        )

    else:
        places = {"health_region_id": "Regional", "state_num_id": "Estado"}
        st.write(
            f"""
            <div class="base-wrapper">
                    <span class="section-header primary-span">Simule o impacto de diferentes ritmos de contágio no seu sistema hospitalar</span>
                    <br><br>
                    <span>Agora é a hora de se preparar para evitar a sobrecarga hospitalar. 
                    No momento, em {user_input["locality"]}, não temos dados suficientes para estimativa do ritmo de contágio. 
                    Por isso, <b>iremos simular com a taxa de contágio do seu {places[user_input["rt_level"]]}, que está entre {str(user_input["rt_values"]["best"])}-{str(user_input["rt_values"]["worst"])}</b>, 
                    ou seja, cada pessoa doente infectará em média entre outras {str(user_input["rt_values"]["best"])}-{str(user_input["rt_values"]["worst"])} pessoas.
                    </span>
            </div>""",
            unsafe_allow_html=True,
        )
    # CHANGE DATA SECTION
    utils.genInputCustomizationSectionHeader(user_input["locality"])
    old_user_input = dict(user_input)
    user_input, session_state = utils.genInputFields(user_input, config, session_state)

    if session_state.reset:
        session.rerun()
    if session_state.update:
        opening_response = user_analytics.log_event(
            "updated sim_numbers",
            {
                "beds_change": session_state.number_beds
                - int(old_user_input["number_beds"]),
                "icu_beds_change": session_state.number_icu_beds
                - int(old_user_input["number_icu_beds"]),
                "cases_change": session_state.number_cases
                - int(old_user_input["population_params"]["I_confirmed"]),
                "deaths_change": session_state.number_deaths
                - int(old_user_input["population_params"]["D"]),
            },
        )
        session_state.update = False
        session.rerun()

    dic_scenarios = {
        "Cenário Estável: O que acontece se seu ritmo de contágio continuar constante?": "estavel",
        "Cenário Negativo: O que acontece se dobrar o seu ritmo de contágio?": "negativo",
        "Cenário Positivo: O que acontece se seu ritmo de contágio diminuir pela metade?": "positivo",
    }

    option = st.selectbox(
        "",
        ["Selecione uma mudança no seu ritmo de contágio"] + list(dic_scenarios.keys()),
    )

    if option == "Selecione uma mudança no seu ritmo de contágio":
        pass

    else:
        # calculate recovered cases
        user_input = _calculate_recovered(data, user_input)

        # SIMULATOR SCENARIOS: BEDS & RESPIRATORS
        user_input["strategy"] = dic_scenarios[option]
        if user_input["strategy"] == "estavel":
            user_analytics.log_event("picked stable_scenario")
        elif user_input["strategy"] == "positivo":
            user_analytics.log_event("picked positive_scenario")
        elif user_input["strategy"] == "negativo":
            user_analytics.log_event("picked negative_scenario")

        # Caso o usuário altere os casos confirmados, usamos esse valor para a estimação
        if (session_state.number_cases is not None) and (
            session_state.number_cases != user_input["population_params"]["I_compare"]
        ):
            user_input["population_params"]["I"] = session_state.number_cases

        # Roda a simulação
        dfs = simulator.run_simulation(_prepare_simulation(user_input, config), config)
        dday_beds = simulator.get_dday(dfs, "I2", int(user_input["number_beds"]))

        dday_icu_beds = simulator.get_dday(
            dfs, "I3", int(user_input["number_icu_beds"])
        )

        utils.genChartSimulationSection(
            SimulatorOutput(
                # color=BackgroundColor.SIMULATOR_CARD_BG,
                min_range_beds=dday_beds["worst"],
                max_range_beds=dday_beds["best"],
                min_range_icu_beds=dday_icu_beds["worst"],
                max_range_icu_beds=dday_icu_beds["best"],
            ),
            plot_simulation(dfs, user_input),
        )


if __name__ == "__main__":
    pass
