import streamlit as st
from streamlit.server.Server import Server
from datetime import datetime
from datetime import timedelta
from typing import List, Dict
import session
from models import (
    SimulatorOutput,
    ContainmentStrategy,
    ResourceAvailability,
    BackgroundColor,
    Logo,
    Link,
    Indicator,
    AlertBackground,
    IndicatorBackground,
    Illustration,
    Product,
    Dimension,
)
from typing import List
import re
import numpy as np
import math
import pandas as pd
import os

import collections
import functools
import inspect
import textwrap
import yaml
import random
from ua_parser import user_agent_parser
import time
import loader

configs_path = os.path.join(os.path.dirname(__file__), "configs")
cities = pd.read_csv(os.path.join(configs_path, "cities_table.csv"))
states = pd.read_csv(os.path.join(configs_path, "states_table.csv"))

config = yaml.load(open("configs/config.yaml", "r"), Loader=yaml.FullLoader)

# DATASOURCE TOOLS


def get_inloco_url(config):

    api_inloco = dict()

    if os.getenv("IS_LOCAL") == "TRUE":
        api_url = config["br"]["api"]["local"]
    else:
        api_url = config["br"]["api"]["external"]

    if os.getenv("INLOCO_CITIES_ROUTE") and os.getenv("INLOCO_STATES_ROUTE"):
        api_inloco["cities"] = api_url + os.getenv("INLOCO_CITIES_ROUTE")
        api_inloco["states"] = api_url + os.getenv("INLOCO_STATES_ROUTE")

    else:
        raise ValueError("Inloco routes not found in env vars!")

    return api_inloco


# DATES TOOLS


def fix_dates(df):
    for col in df.columns:
        if "last_updated" in col:
            df[col] = pd.to_datetime(
                df[col]
            )  # .apply(lambda x: x.strftime("%d/%m/%Y"))
    return df


def convert_times_to_real(row):
    today = datetime.now()
    return today + timedelta(row["ddias"])


def dday_preffix(dday):
    if dday > 30:
        return "+ 30"
    else:
        return "até " + str(dday)


# TODO: melhorar essa funcao
def get_sources(user_input, data, cnes_sources, resources):

    cols_agg = {
        "number": lambda x: x.sum() if np.isnan(x.sum()) == False else 0,
        "last_updated_number": lambda x: pd.to_datetime(x).max(),
        "author_number": lambda x: x.drop_duplicates().str.cat(),
    }

    for x in resources:

        for item in cols_agg.keys():

            col = "_".join([item, x])

            if user_input["place_type"] == "city_id":  # usa dados da regional
                place_type = "health_region_id"
            else:
                place_type = user_input["place_type"]

            user_input[col] = cnes_sources[
                cnes_sources[place_type] == data[place_type].iloc[0]
            ][col].agg(cols_agg[item])

    user_input["last_updated_number_beds"] = pd.to_datetime(
        user_input["last_updated_number_beds"]
    ).strftime("%d/%m")

    user_input["last_updated_number_icu_beds"] = pd.to_datetime(
        user_input["last_updated_number_icu_beds"]
    ).strftime("%d/%m")

    return user_input


# PLACES TOOLS


def add_all(x, all_string="Todos", first=None):
    formatted = [all_string] + list(x)
    if first != None:
        first_index = formatted.index(first)
        item = formatted.pop(first_index)
        formatted.insert(0, item)
    return formatted


def filter_place(
    dfs, place_type, state_name=None, health_region_name=None, city_name=None
):

    if place_type == "state":
        return dfs["city"]["state_name"].sort_values().unique()
    elif place_type == "city":
        data = dfs["city"][dfs["city"]["state_name"] == state_name]
        if health_region_name != None and health_region_name != "Todos":
            data = data.loc[data["health_region_name"] == health_region_name]
        return add_all(data["city_name"].sort_values().unique())
    else:
        data = dfs["city"][dfs["city"]["state_name"] == state_name]
        return add_all(data["health_region_name"].sort_values().unique())


def choose_place(city, region, state):
    if city == "Todos" and region == "Todos":
        return state + " (Estado)"
    if city == "Todos":
        return region + " (Região de Saúde)"
    return city


class Dictionary:
    def __init__(self):
        self.dictionary = None

    def check_initialize(self):
        if self.dictionary is None:
            self.dictionary = loader.read_data(
                "br",
                loader.config,
                loader.config["br"]["api"]["endpoints"]["utilities"]["place_ids"],
            )

    def get_place_names_by_id(self, id):
        self.check_initialize()
        if id < 100:  # is state
            return [
                self.dictionary.loc[self.dictionary["state_num_id"] == id][
                    "state_name"
                ].values[0]
            ]
        elif id < 10000:  # is health regional
            row = self.dictionary.loc[self.dictionary["health_region_id"] == id]
            # healh regional,stater
            return [
                row["health_region_name"].values[0],
                row["state_name"].values[0],
            ]
        else:  # is city
            row = self.dictionary.loc[self.dictionary["city_id"] == id]
            # city,healh regional,state
            return [
                row["city_name"].values[0],
                row["health_region_name"].values[0],
                row["state_name"].values[0],
            ]

    def get_place_id_by_names(
        self, state_name, city_name="Todos", health_region_name=None
    ):
        self.check_initialize()
        dictionary = self.dictionary.loc[self.dictionary["state_name"] == state_name]
        if health_region_name != None:
            return dictionary.loc[
                dictionary["health_system_region"] == health_region_name
            ]["health_region_id"].values[0]
        elif city_name != "Todos":
            return dictionary.loc[dictionary["city_name"] == city_name][
                "city_id"
            ].values[0]
        else:
            dictionary["state_num_id"].values[0]

    def get_state_alphabetical_id_by_name(self, state_name):
        self.check_initialize()
        if state_name == "Todos":
            return "BR"
        return self.dictionary.loc[self.dictionary["state_name"] == state_name][
            "state_id"
        ].values[0]


# def get_state_str_id_by_id(place_id):

#     states = pd.read_csv(
#         os.path.join(
#             os.path.join(os.path.dirname(__file__), "configs"), "states_table.csv"
#         )
#     )

#     index = [i for i in states.columns].index("state_id")
#     return states.query("state_num_id == '%s'" % place_id).values[0][index]


def get_ufs_list():

    return [
        "AC",
        "AL",
        "AM",
        "AP",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MG",
        "MS",
        "MT",
        "PA",
        "PB",
        "PE",
        "PI",
        "PR",
        "RJ",
        "RN",
        "RO",
        "RR",
        "RS",
        "SC",
        "SE",
        "SP",
        "TO",
    ]


# FRONT-END TOOLS
# AMPLITUDE ANALYTICS HELPER METHODS
# PLUS SOME EXTRA STREAMLIT HACKING
# Kept for backwards compatibility reasons
def get_server_session():
    return session._get_session_raw()


def manage_user_existence(user_session, session_state):
    """ 
        Decides if the user is new or not and if it is new generates a random id 
        Will not try to do it twice because we can have the case of the user refusing to hold our cookies
        therefore we will consider him the anonymous user and give up trying to give him our cookie.
    """
    user_data = parse_headers(user_session.ws.request)
    if session_state.already_generated_user_id is None:
        session_state.already_generated_user_id = False

    if user_data["cookies_initialized"] is False:
        # Sometimes the browser doesn't load up upfront so we need this
        reload_window()
        time.sleep(1)
    else:
        if (
            "user_unique_id" not in user_data["Cookie"].keys()
            and session_state.already_generated_user_id is False
        ):
            hash_id = gen_hash_code(size=32)
            session_state.already_generated_user_id = True
            update_user_public_info()
            time.sleep(0.1)
            give_cookies("user_unique_id", hash_id, 99999, True)


def gen_hash_code(size=16):
    return "".join(
        random.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuv")
        for i in range(size)
    )


def parse_headers(request):
    """ Takes a raw streamlit request header and converts it to a nicer dictionary """
    data = dict(request.headers.items())
    ip = request.remote_ip
    if "Cookie" in data.keys():
        data["Cookie"] = dict([i.split("=") for i in data["Cookie"].split("; ")])
        data["cookies_initialized"] = True
    else:
        data["Cookie"] = dict()
        data["cookies_initialized"] = False
    if "user_public_data" in data["Cookie"].keys():
        data["Cookie"]["user_public_data"] = dict(
            [i.split("|:") for i in data["Cookie"]["user_public_data"].split("|%")]
        )
    data["Remote_ip"] = ip
    data.update(parse_user_agent(data["User-Agent"]))
    return data


def parse_user_agent(ua_string):
    in_data = user_agent_parser.Parse(ua_string)
    out_data = dict()
    data_reference = [
        ["os_name", ["os", "family"]],
        ["os_version", ["os", "major"]],
        ["device_manufacturer", ["device", "brand"]],
        ["device_model", ["device", "model"]],
        ["platform", ["user_agent", "family"]],
        ["app_version", ["user_agent", "major"]],
    ]
    for key_in, keys_out in data_reference:
        try:
            out_data["ua_" + key_in] = in_data[keys_out[0]][keys_out[1]]
        except:
            out_data["ua_" + key_in] = None
    return out_data


def give_cookies(cookie_name, cookie_info, cookie_days=99999, rerun=False):
    """ Gives the user a browser cookie """
    # Cookie days is how long in days will the cookie last
    st.write(
        f"""<iframe src="resources/cookiegen.html?cookie_name={cookie_name}&cookie_value={cookie_info}&cookies_days={cookie_days}" height="0" width="0" style="border: 1px solid black; float: right;"></iframe>""",
        unsafe_allow_html=True,
    )
    if rerun:
        time.sleep(1)
        reload_window()
        # session.rerun()


def update_user_public_info():
    """ updates the user's public data for us like his ip address and geographical location """
    st.write(
        f"""
        <iframe src="resources/cookiegen.html?load_user_data=true" height="0" width="0" style="border: none; float: right;"></iframe>""",
        unsafe_allow_html=True,
    )


def reload_window():
    """ Reloads the user's entire browser window """
    st.write(
        f"""
        <iframe src="resources/window_reload.html?load_user_data=true" height="0" width="0" style="border: none; float: right;"></iframe>""",
        unsafe_allow_html=True,
    )
    time.sleep(1)


# END OF AMPLITUDE HELPER METHODS

# JAVASCRIPT HACK METHODS


def stylizeButton(name, style_string, session_state, others=dict()):
    """ adds a css option to a button you made """
    session_state.button_styles[name] = [style_string, others]


def applyButtonStyles(session_state):
    """ Use it at the end of the program to apply styles to buttons as defined by the function above """
    time.sleep(0.1)
    html = ""
    for name, style in session_state.button_styles.items():
        parts = (
            style[0]
            .replace("\n", "")
            .replace("    ", "")
            .replace("; ", "&")
            .replace(";", "&")
            .replace(":", "=")
        )
        other_args = "&".join(
            [str(key) + "=" + str(value) for key, value in style[1].items()]
        )
        html += f"""
        <iframe src="resources/redo-button.html?name={name}&{parts}&{other_args}" style="height:0px;width:0px;">
        </iframe>"""
    st.write(html, unsafe_allow_html=True)


def get_radio_horizontalization_html(radio_label):
    """ Takes a normal radio and restilizes it to make it horizontal and bigger"""
    html = f"""<iframe src="resources/horizontalize-radio.html?radioText={radio_label}" style="height:0px;width:0px;"></iframe>"""
    return html


def hide_iframes():
    st.write(
        f"""<iframe src="resources/hide-iframes.html" height = 0 width = 0></iframe>""",
        unsafe_allow_html=True,
    )


# END OF JAVASCRIPT HACK METHODS


def gen_pdf_report():
    st.write(
        """
    <iframe src="resources/ctrlp.html" height="100" width="350" style="border:none; float: right;"></iframe>
    """,
        unsafe_allow_html=True,
    )


def make_clickable(text, link):
    # target _blank to open new window
    # extract clickable text to display for your link
    return f'<a target="_blank" href="{link}">{text}</a>'


def localCSS(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def gen_whatsapp_button(info) -> None:
    """Generate WPP button

    Args:
        info: config["contact"]
    """
    url = "whatsapp://send?text={}&phone=${}".format(info["msg"], info["phone"])
    st.write(
        """ 
         <a href="%s" class="float" target="_blank" id="messenger">
                <i class="material-icons">?</i>
                <p class="float-header">Dúvidas?</p></a>
        """
        % url,
        unsafe_allow_html=True,
    )


def gen_info_modal(config):
    situation_classification = config["br"]["farolcovid"]["rules"][
        "situation_classification"
    ]["cuts"]
    control_classification = config["br"]["farolcovid"]["rules"][
        "control_classification"
    ]["cuts"]
    capacity_classification = config["br"]["farolcovid"]["rules"][
        "capacity_classification"
    ]["cuts"]
    trust_classification = config["br"]["farolcovid"]["rules"]["trust_classification"][
        "cuts"
    ]

    date_update = config["br"]["farolcovid"]["date_update"]

    return f"""
    <a href="#entenda-mais" class="info-btn">Entenda a classificação dos níveis</a>
    <div id="entenda-mais" class="info-modal-window">
        <div>
            <a href="#" title="Close" class="info-btn-close" style="color: white;">&times</a>
            <div style="margin: 10px 15px 15px 15px;">
            <h1 class="primary-span">Valores de referência</h1>
            <div style="font-size: 12px">
                <b>Atualizado em</b>: {date_update}<br>
            </div>
            <div class="info-div-table">
            <table class="info-table">
            <tbody>
                <tr>
                    <td class="grey-bg"><strong>Dimensão</strong></td>
                    <td class="grey-bg"><strong>Indicador</strong></td>
                    <td class="grey-bg"><strong>Novo Normal</strong></td>
                    <td class="grey-bg"><strong>Risco Moderado</strong></td>
                    <td class="grey-bg"><strong>Risco Alto</strong></td>
                    <td class="grey-bg"><strong>Risco Altíssimo</strong></td>
                </tr>
                <tr>
                    <td rowspan="2">
                    <p><span>Situação da doença</span></p><br/>
                    </td>
                    <td><span>Novos casos diários (Média móvel 7 dias)</span></td>
                    <td class="light-blue-bg bold"><span>x&lt;={situation_classification[1]}</span></td>
                    <td class="light-yellow-bg bold"><span>{situation_classification[1]}&lt;x&lt;={situation_classification[2]}</span></td>
                    <td class="light-orange-bg bold"><span>{situation_classification[2]}&lt;=x&lt;={situation_classification[3]}</span></td>
                    <td class="light-red-bg bold"><span>x &gt;= {situation_classification[3]} </span></td>
                </tr>
                <tr>
                    <td><span>Tendência de novos casos diários</span></td>
                    <td class="lightgrey-bg" colspan="4"><span>Se crescendo*, mover para o nível mais alto</span></td>
                </tr>
                <tr>
                    <td><span>Controle da doença</span></td>
                    <td><span>Número de reprodução efetiva</span></td>
                    <td class="light-blue-bg bold"><span>&lt;{control_classification[1]}</span></td>
                    <td class="light-yellow-bg bold"><span>&lt;{control_classification[1]} - {control_classification[2]}&gt;</span></td>
                    <td class="light-orange-bg bold"><span>&lt;{control_classification[2]} - {control_classification[3]}&gt;</span>&nbsp;</td>
                    <td class="light-red-bg bold"><span>&gt;{control_classification[3]}</span></td>
                </tr>
                <tr>
                    <td><span>Capacidade de respostas do sistema de saúde</span></td>
                    <td><span>Projeção de tempo para ocupação total de leitos UTI</span></td>
                    <td class="light-blue-bg bold">{capacity_classification[3]} - 90 dias</td>
                    <td class="light-yellow-bg bold"><span>{capacity_classification[2]} - {capacity_classification[3]} dias</span></td>
                    <td class="light-orange-bg bold"><span>{capacity_classification[1]} - {capacity_classification[2]} dias</span></td>
                    <td class="light-red-bg bold"><span>{capacity_classification[0]} - {capacity_classification[1]} dias</span></td>
                </tr>
                <tr>
                    <td><span>Confiança dos dados</span></td>
                    <td><span>Subnotificação (casos <b>não</b> diagnosticados a cada 10 infectados)</span></td>
                    <td class="light-blue-bg bold"><span>{int(trust_classification[0]*10)}&lt;=x&lt;{int(trust_classification[1]*10)}</span></td>
                    <td class="light-yellow-bg bold"><span>{int(trust_classification[1]*10)}&lt;=x&lt;{int(trust_classification[2]*10)}</span></td>
                    <td class="light-orange-bg bold"><span>{int(trust_classification[2]*10)}&lt;=x&lt;{int(trust_classification[3]*10)}</span></td>
                    <td class="light-red-bg bold"><span>{int(trust_classification[3]*10)}&lt;=x&lt;=10</span></td>
                </tr>
            </tbody>
            </table>
            </div>
            <div style="font-size: 12px">
                * Como determinamos a tendência:
                <ul class="sub"> 
                    <li> Crescendo: caso o aumento de novos casos esteja acontecendo por pelo menos 5 dias. </li>
                    <li> Descrescendo: caso a diminuição de novos casos esteja acontecendo por pelo menos 14 dias. </li>
                    <li> Estabilizando: qualquer outra mudança. </li>
                </ul>
            </div>
            <div style="font-size: 14px">
                Para mais detalhes confira nossa página de Metodologia no menu lateral</a>.
            </div>
            </div>
        </div>
    </div>"""


# VIEW COMPONENTS FAROLCOVID


def genHeroSection(title1: str, title2: str, subtitle: str, logo: str, header: bool):

    if header:
        header = """<a href="https://coronacidades.org/" target="blank" class="logo-link"><span class="logo-bold">corona</span><span class="logo-lighter">cidades</span></a>"""
    else:
        header = """<br>"""

    # Info
    banner = f"""<a href="#novidades" class="info-btn" style:"margin-left:1em">Veja como navegar</a>
        <div id="novidades" class="nov-modal-window">
            <div>
                <a href="#" title="Close" class="info-btn-close" style="color: white;">&times</a>
                <div style="margin: 10px 15px 15px 15px;">
                    <h1 class="primary-span">Saiba como cada ferramenta apoia a resposta ao coronavírus</h1>
                    <p class="darkblue-span uppercase"> <b>Farol Covid</b> </p>
                    <img class="img-modal" src={config["br"]["icons"]["farolcovid_logo"]} alt="Ícone Farol Covid">
                    <div>
                        <p> <b>Importante: mudamos a metodologia dos indicadores - veja mais em Modelos, limitações e fontes no menu lateral.</b> Descubra o nível de alerta do estado, regional de saúde ou município de acordo com os indicadores:</p>
                        - <b>Situação da doença</b>: média de novos casos 100 mil por habitantes;</br>
                        - <b>Controle da doença</b>: taxa de contágio</br>
                        - <b>Capacidade do sistema</b>: tempo para ocupação de leitos UTI</br>
                        - <b>Confiança de dados</b>: taxa de subnotificação de casos</br><br>
                    </div>
                    <div>
                    <p class="darkblue-span uppercase"> <b>SimulaCovid</b> </p>
                    <img class="img-modal" src=%s alt="Ícone SimulaCovid">  
                    <p style="height:100px;">Simule o que pode acontecer com o sistema de saúde local se o ritmo de contágio aumentar 
                        ou diminuir e planeje suas ações para evitar a sobrecarga hospitalar.</p>
                    </div>
                    <div>
                    <p class="darkblue-span uppercase"> <b>Distanciamento Social</b> </p>
                    <img class="img-modal" src={config["br"]["icons"]["distanciamentosocial_logo"]} alt="Ícone Distanciamento Social">
                        <p style="height:100px;">Acompanhe a atualização diária do índice e descubra como está a circulação de pessoas 
                            e o distanciamento social no seu estado ou município.    
                        </p>
                    </div>
                    <div>
                    <p class="darkblue-span uppercase"> <b>Saúde em Ordem</b> </p>
                    <img class="img-modal" src={config["br"]["icons"]["saudeemordem_logo"]} alt="Ícone Saúde em Ordem">
                    <p> Entenda quais atividades deveriam reabrir primeiro no seu estado ou regional, considerando:
                        - <b>Segurança Sanitária</b>: quais setores têm menor exposição à Covid-19?</br>
                        - <b>Contribuição Econômica</b>: quais setores movimentam mais a economia local?</br></p>
                    <p> </p>
                    </div>
                    <div>
                    <p class="darkblue-span uppercase"> <b>Onda Covid</b> </p>
                    <img class="img-modal" src={config["br"]["icons"]["ondacovid_logo"]} alt="Ícone Onda Covid">
                    <p>Com base no número de óbitos de Covid-19 registrados, acompanhe se seu município já saiu do pico da doença. </p>
                    </div>
                </div>
            </div>"""

    st.write(
        f"""
        <div class="base-wrapper hero-bg">
            <div class="hero-wrapper">
                <div class="hero-container-content">
                    {header}
                    <span class="hero-container-product primary-span">{title1}<br/>{title2}</span>
                    <span class="hero-container-subtitle primary-span">{subtitle}</span>
                </div>
                <div class="hero-container-image">   
                    <img style="width: 100%;" src={logo}/>
                </div>
            </div>
            <div class="hero-container-content">
                <br>{banner}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def genInputFields(user_input, config, session):

    # # Inicia sem update
    # session.update = False

    authors_beds = user_input["author_number_beds"]
    beds_update = user_input["last_updated_number_beds"]

    authors_icu_beds = user_input["author_number_icu_beds"]
    icu_beds_update = user_input["last_updated_number_icu_beds"]

    print("\nSESSION_STATE:", session.number_beds, session.number_icu_beds)

    if session.reset or session.number_beds == None:
        number_beds = int(
            user_input["number_beds"]
            * config["br"]["simulacovid"]["resources_available_proportion"]
        )
        number_icu_beds = int(
            user_input["number_icu_beds"]
            * config["br"]["simulacovid"]["resources_available_proportion"]
        )
        number_cases = int(user_input["population_params"]["I_confirmed"])
        number_deaths = int(user_input["population_params"]["D"])
        session.reset = False
    else:
        number_beds = int(session.number_beds)
        number_icu_beds = int(session.number_icu_beds)
        number_cases = int(session.number_cases)
        number_deaths = int(session.number_deaths)

    cases_update = pd.to_datetime(user_input["last_updated_cases"]).strftime("%d/%m")

    locality = user_input["locality"]

    if locality == "Brasil":
        authors_beds = "SUS e Embaixadores"
        authors_icu_beds = "SUS e Embaixadores"

    user_input["number_beds"] = st.number_input(
        f"Número de leitos destinados aos pacientes com Covid-19 (50% do reportado em {authors_beds}; atualizado: {beds_update})",
        0,
        None,
        number_beds,
    )

    user_input["number_icu_beds"] = st.number_input(
        f"Número de leitos UTI destinados aos pacientes com Covid-19 (100% do reportado em {authors_icu_beds}; atualizado: {icu_beds_update}):",
        0,
        None,
        number_icu_beds,
    )

    user_input["population_params"]["I_confirmed"] = st.number_input(
        f"Casos confirmados (fonte: Brasil.IO; atualizado: {cases_update}):",
        0,
        None,
        number_cases,
    )

    user_input["population_params"]["D"] = st.number_input(
        f"Mortes confirmadas (fonte: Brasil.IO; atualizado: {cases_update}):",
        0,
        None,
        number_deaths,
    )

    # Faz o update quando clica o botão
    if st.button("Finalizar alteração"):

        print("FINALIZADO:", user_input)

        session.number_beds = int(user_input["number_beds"])
        session.number_icu_beds = int(user_input["number_icu_beds"])
        session.number_cases = int(user_input["population_params"]["I_confirmed"])
        session.number_deaths = int(user_input["population_params"]["D"])

        session.update = True
    else:
        session.update = False

    if st.button("Resetar aos valores oficais"):
        session.reset = True

    # Estiliza botão
    alteration_button_style = """border: 1px solid var(--main-white);box-sizing: border-box;border-radius: 15px; width: auto;padding: 0.5em;text-transform: uppercase;font-family: var(--main-header-font-family);color: var(--main-white);background-color: var(--main-primary);font-weight: bold;text-align: center;text-decoration: none;font-size: 14px;animation-name: fadein;animation-duration: 3s;margin-top: 1em;"""
    reset_button_style = """position:absolute;right:3em;top:-68px;border: 1px solid var(--main-white);box-sizing: border-box;border-radius: 15px; width: auto;padding: 0.5em;text-transform: uppercase;font-family: var(--main-header-font-family);color: var(--main-white);background-color: rgb(160,170,178);font-weight: bold;text-align: center;text-decoration: none;font-size: 14px;animation-name: fadein;animation-duration: 3s;margin-top: 1em;"""
    stylizeButton(
        "Finalizar alteração", alteration_button_style, session,
    )
    stylizeButton(
        "Resetar aos valores oficais", reset_button_style, session,
    )
    return user_input, session


# TODO: not used
def translate_risk(risk_value):
    if risk_value == "nan":
        return "Indef"
    else:
        try:
            return loader.config["br"]["farolcovid"]["categories"][risk_value]
        except:
            return risk_value


def genAnalysisDimmensionsCard(dimension: Dimension):
    return f"""<div style="margin-top: 0px; display: inline-block; top:0x;">
            <div class="dimension-card primary-span style="top:0x; padding-left: 24px; padding-top: 24px; padding-right: 24px;">
                {dimension.text}
            </div>
        </div>"""


def genAnalysisDimmensionsSection(dimensions: List[Dimension]):
    cards = list(map(genAnalysisDimmensionsCard, dimensions))
    cards = "".join(cards)

    st.write(
        f"""<div class="container">
        <div class="base-wrapper primary-span">
            <div>
                <span class="section-header">DIMENSÕES DA ANÁLISE</span>
            </div>
            <span class="p3">O que olhamos ao avaliar o cenário da pandemia em um lugar?</span>
            <div class="flex flex-row mt flex-m-column" style="margin-bottom: 0px;height:auto; display:inline-block top:0x;">
            {cards}
            </div>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )


def genIndicatorCard(indicator: Indicator, place_type: str, rt_type: str = "nan"):

    if indicator.display == "None":
        indicator.display = ""
        indicator.unit = ""

    # Get name of alert by number
    if indicator.risk == "nan":
        alert = ""
    else:
        alert = loader.config["br"]["farolcovid"]["categories"][int(indicator.risk)]

    if indicator.right_display == "estabilizando":
        indicator_right_display = "estabilizando em " + alert
    else:
        indicator_right_display = indicator.right_display

    # TODO: find better palce to save this dic
    captions_by_place = {
        "state_num_id": {
            "SITUAÇÃO DA DOENÇA": "Hoje em seu <b>estado</b> são <b>reportados</b> em média",
            "CONTROLE DA DOENÇA": "Não há dados abertos sistematizados de testes ou rastreamento de contatos no Brasil. Logo, <b>classificamos pela estimativas de Rt de seu estado.</b>",
            "CAPACIDADE DO SISTEMA": "Se nada mudar, a capacidade hospitalar de seu <b>estado</b> será atingida em",
            "CONFIANÇA DOS DADOS": "A cada 10 pessoas infectadas em seu <b>estado</b>,",
        },
        "health_region_id": {
            "SITUAÇÃO DA DOENÇA": "Hoje em sua <b>regional de saúde</b> são <b>reportados</b> em média",
            "CONTROLE DA DOENÇA": "Não há dados abertos sistematizados de testes ou rastreamento de contatos no Brasil. Logo, <b>classificamos pela estimativas de Rt de sua regional.</b>",
            "CAPACIDADE DO SISTEMA": "Se nada mudar, a capacidade hospitalar de sua <b>regional de saúde</b> será atingida em",
            "CONFIANÇA DOS DADOS": "A cada 10 pessoas infectadas em sua <b>regional de saúde</b>,",
        },
        "city_id": {
            "SITUAÇÃO DA DOENÇA": "Hoje em seu <b>município</b> são <b>reportados</b> em média",
            "CONTROLE DA DOENÇA": {
                "health_region_id": "Não há dados abertos sistematizados de testes ou rastreamento de contatos no Brasil. Logo, <b>classificamos pela estimativas de Rt de sua regional.</b>",
                "city_id": "Não há dados abertos sistematizados de testes ou rastreamento de contatos no Brasil. Logo, <b>usamos estimativas de Rt de seu município para classificação.</b>",
            },
            "CAPACIDADE DO SISTEMA": "Se nada mudar, a capacidade hospitalar de sua <b>regional de saúde</b> será atingida em",
            "CONFIANÇA DOS DADOS": "A cada 10 pessoas infectadas em sua <b>regional de saúde</b>,",
        },
    }

    if place_type == "city_id" and indicator.header == "CONTROLE DA DOENÇA":
        indicator.caption = captions_by_place[place_type][indicator.header][rt_type]
    else:
        indicator.caption = captions_by_place[place_type][indicator.header]

    return f"""
    <div class="main-indicator-card flex flex-column mr" style="z-index:1;display:inline-block;position:relative;">
        <span class="main-card-header-v2">{indicator.header}</span>
        <span class="main-card-list-v2">{indicator.caption}</span>
        <div class="flex flex-row flex-justify-space-between mt" style="width:250px;">
        </div>
        <span class="bold p2 main-card-display-value">{indicator.display}<span class="bold p5">  {indicator.unit}</span></span>
        <div class="{IndicatorBackground(try_int(indicator.risk)).name}-alert-bg risk-pill " style="position:absolute;bottom:120px;">
            <span class="bold white-span p4">{alert}</span>
        </div>
        <div class="main-card-display-text-v2 sdcardtext-left">
                <span class="lighter">{indicator.left_label}<br></span>
                <span class="bold">{indicator.left_display}</span>
        </div>
        <div class="main-card-display-text-v2 sdcardtext-right">
                <span class="lighter">{indicator.right_label}<br></span>
                <span class="bold">{indicator_right_display}</span>
        </div>
        <div class="last-updated-text">Atualizado em: {indicator.last_updated}</div>
    </div>"""


def genKPISection(
    place_type: str,
    locality: str,
    alert: str,
    indicators: Dict[str, Indicator],
    n_colapse_regions: int = 0,
    rt_type: str = "nan",
):
    # Genetate cards HTML
    cards = "".join(
        [genIndicatorCard(group, place_type, rt_type) for group in indicators.values()]
    )
    # print(cards)
    info_modal = gen_info_modal(config)

    # Generate subheader
    if not isinstance(alert, str):
        bg = "gray"
        alert = "Sem classificação"
        caption = "Sugerimos que confira o nível de risco de seu estado ou regional de saúde. <br/>Seu município não possui dados consistentes suficientes para calcularmos o nível de risco."
        stoplight = "%0a%0a"
    else:
        bg = AlertBackground(alert).name
        if alert == "altíssimo":
            caption = f"Nível de alerta <b>{alert.upper()}</b>: há um crescente número de casos de Covid-19 e grande parte deles não são detectados."
        elif alert == "alto":
            caption = f"Nível de alerta <b>{alert.upper()}</b>: há muitos casos de Covid-19 com transmissão comunitária. A presença de casos não detectados é provável."
        elif alert == "moderado":
            caption = f"Nível de alerta <b>{alert.upper()}</b>: há um número moderado de casos e a maioria tem uma fonte de transmissão conhecida."
        elif alert == "novo normal":
            caption = f"Nível de alerta <b>{alert.upper()}</b>: casos são raros e técnicas de rastreamento de contato e monitoramento de casos suspeitos evitam disseminação."

        if "state" in place_type:
            if n_colapse_regions > 0:
                caption = f"{caption}<br><b>Note que {n_colapse_regions} regionais de saúde avaliadas estão em Alerta Alto ou Altíssimo</b>. Sugerimos que políticas de resposta à Covid-19 sejam avaliadas a nível subestatal."
            else:
                caption = f"{caption}<br>Nenhuma regional de saúde avaliada está em Alerta Alto ou Altíssimo de colapso. Sugerimos que políticas de resposta à Covid-19 sejam avaliadas a nível subestatal."

    msg = f"""🚨 *BOLETIM CoronaCidades |  {locality}, {datetime.now().strftime('%d/%m')}*  
    🚨%0a%0aNÍVEL DE ALERTA: {alert.upper()}
    %0a%0a😷 *SITUAÇÃO DA DOENÇA*: Hoje são reportados❗em média *{indicators['situation'].display} casos por 100mil habitantes.
    %0a%0a *CONTROLE DA DOENÇA*: A taxa de contágio mais recente é de *{indicators['control'].left_display}* - ou seja, uma pessoa infecta em média *{indicators['control'].left_display}* outras.
    %0a%0a🏥 *CAPACIDADE DO SISTEMA*: A capacidade hospitalar será atingida em *{str(indicators['capacity'].display).replace("+", "mais")} meses* 
    %0a%0a🔍 *CONFIANÇA DOS DADOS*: A cada 10 pessoas infectadas, *{indicators['trust'].display} são diagnosticadas* 
    %0a%0a👉 Saiba se seu município está no nível de alerta baixo, médio ou alto acessando o *FarolCovid* aqui: https://coronacidades.org/farol-covid/"""
    # msg = "temporarily disabled"

    # Write cards section
    st.write(
        """<div class="container">
        <div class="alert-banner %s-alert-bg mb" style="margin-bottom: 0px;height:auto;">
                <div class="base-wrapper flex flex-column" style="margin-top: 0px;">
                        <div class="flex flex-row flex-space-between flex-align-items-center">
                         <span class="white-span header p1">%s</span>
                         <a class="btn-wpp" href="whatsapp://send?text=%s" target="blank">Compartilhar no Whatsapp</a>
                         </div>
                        <span class="white-span p3">%s</span>
                        <div class="flex-row flex-m-column">%s</div>
                        <div class = "info">%s</div>
                </div>
        </div>
        </div>
        <div class='base-wrapper product-section'></div>
        """
        % (bg, locality, msg, caption, cards, info_modal),
        unsafe_allow_html=True,
    )


def genProductCard(product: Product):
    if product.recommendation == "Sugerido":
        badge_style = "primary-bg"
    elif product.recommendation == "Risco alto":
        product.recommendation = "Espere"
        badge_style = f"red-alert-bg"
    elif product.recommendation == "Risco baixo":
        product.recommendation = "Explore"
        badge_style = "primary-bg"
    else:
        badge_style = "primary-bg"

    return f"""<div class="flex flex-column elevated pr pl product-card mt  ">
                <img src="{product.image}" style="height:100px;" class="card-image mt"/>
                <div class="flex flex-row">
                        <span class="p3 header bold uppercase">{product.name}</span>
                </div>
                <span class="selection-card-caption">{product.caption}</span>
                <span class="{badge_style} ml secondary-badge">{product.recommendation}</span>
                </div>
                """


def genProductsSection(products: List[Product]):
    cards = list(map(genProductCard, products))
    cards = "".join(cards)

    st.write(
        f"""
        <div class="base-wrapper">
                <span class="section-header primary-span">O QUE MAIS VOCÊ QUER SABER SOBRE O SEU MUNICÍPIO?</span>
                <div class="flex flex-row flex-space-around mt flex-m-column">{cards}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def genInputCustomizationSectionHeader(locality: str) -> None:
    st.write(
        """
        <div class="base-wrapper">
                <span class="section-header primary-span">Verifique os dados disponíveis <span class="yellow-span">(%s)</span></span>
                <br><br>
                <span>
                Usamos os dados do Brasil.io e DataSUS, mas é possível que esses dados estejam um pouco desatualizados. Se estiverem, é só ajustar os valores abaixo para continuar a simulação.
                <br><b>Para municípios usamos os dados de leitos da respectiva regional de saúde.</b>
                </span>
                <br>
        </div>"""
        % locality,
        unsafe_allow_html=True,
    )


def gen_footer() -> None:

    st.write(
        """
        <div class="magenta-bg">
                <div class="base-wrapper">
                        <div class="logo-wrapper">
                                <span><b>A equipe do Coronacidades está à disposição para apoiar o gestor público a aprofundar a análise para seu estado ou município, de forma inteiramente gratuita.</b>
                                Também queremos queremos ouvir sua opinião sobre a ferramenta, entre em contato via chat (canto inferior direito). Outras ferramentas e mais recursos para responder à crise da Covid-19 estão disponíveis em nosso site 
                                <a target="_blank" style="color:#3E758A;" href="https://coronacidades.org/">coronacidades.org</a>.</span><br/>
                                <span><b>As análises apresentadas no Farol Covid são indicativas, feitas a partir de dados oficiais públicos e estudos referenciados já publicados, estando sujeitas a variáveis que aqui não podem ser consideradas.</b>
                                Trata-se de contribuição à elaboração de cenários por parte dos governos e não configura qualquer obrigação ou responsabilidade perante as decisões efetivadas.
                                Saiba mais sobre os cálculos por trás de análises e indicadores em nossas páginas de Níveis de Risco e Modelo Epidemiológico (menu lateral esquerdo), 
                                que mantemos atualizadas conforme evoluímos em nossas metodologias.<br><br></span>
                                <span><i>Todo código da ferramenta pode ser acessado no <a target="_blank" class="github-link" href="https://github.com/ImpulsoGov/farolcovid">Github do projeto</a>
                                e os dados estão disponíveis em nossa <a target="_blank" class="github-link" href="https://github.com/ImpulsoGov/coronacidades-datasource/blob/master/README.md">API</a>.</i></span>
                                </br></br></span>
                                <img class="logo-img" src="%s"/>
                                <div class="logo-section">
                                        <img class="logo-img" src="%s"/>
                                        <img class="logo-img" src="%s"/>
                                </div>
                        </div>
                </div>
        </div>"""
        % (Logo.IMPULSO.value, Logo.CORONACIDADES.value, Logo.ARAPYAU.value),
        unsafe_allow_html=True,
    )


# VIEW COMPONENTS SIMULACOVID


def gen_ambassador_section() -> None:

    st.write(
        """
        <br>
        <div class="base-wrapper flex flex-column" style="background-color:#0090A7">
            <div class="white-span header p1" style="font-size:30px;">IMPORTANTE: Usamos dados abertos e históricos para calcular os indicadores.</div><br>
            <span class="white-span"> <b>Quer aprofundar a análise para seu Estado ou Município?</b> A equipe do Coronacidades está disponível de forma inteiramente gratuita!</span>
            <a class="btn-ambassador" href="https://coronacidades.org/fale-conosco/" target="blank">FALE CONOSCO</a>
        </div>""",
        unsafe_allow_html=True,
    )


def genSimulatorOutput(output: SimulatorOutput) -> str:

    beds_img = "https://i.imgur.com/27hutU0.png"
    icu_beds_img = "https://i.imgur.com/Oh4l8qM.png"

    bed_projection = dday_preffix(output.max_range_beds) + " dias"
    icu_bed_projection = dday_preffix(output.max_range_icu_beds) + " dias"

    output = """
        <div>
                <div class="simulator-container simulator-beds-card-bg">
                        <div class="simulator-output-wrapper">
                                <div class="simulator-output-row">
                                        <span class="simulator-output-row-prediction-value">
                                                %s
                                        </span>  
                                </div> 
                                <span class="simulator-output-row-prediction-label">
                                        será atingida a capacidade máxima de <b>leitos</b>
                                </span>
                        </div>
                        <img src="%s" class="simulator-output-image"/>
                </div>
                <br />
                <div class="simulator-container simulator-icu-beds-card-bg">
                        <div class="simulator-output-wrapper">
                                <div class="simulator-output-row">
                                        <span class="simulator-output-row-prediction-value">
                                                %s
                                        </span>  
                                </div> 
                                <span class="simulator-output-row-prediction-label">
                                        meses será atingida a capacidade máxima de <b>leitos UTI</b>
                                </span>
                        </div>
                        <img src="%s" class="simulator-output-image"/>
                </div>
        </div>""" % (
        bed_projection,
        beds_img,
        icu_bed_projection,
        icu_beds_img,
    )

    return output.strip("\n\t")


def genChartSimulationSection(simulation: SimulatorOutput, fig) -> None:

    simulation = genSimulatorOutput(simulation)

    st.write(
        """<div class="lightgrey-bg">
                <div class="base-wrapper">
                        <div class="simulator-header">
                                <span class="section-header primary-span">Aqui está o resultado da sua simulação</span>
                        </div>
                        <div class="simulator-wrapper">
                                %s
                        </div>
                         <div style="display: flex; flex-direction: column; margin-top: 5em"> 
                                <span class="section-header primary-span">Visão detalhada da sua simulação</span><br>
                                <span style="border-radius: 15px; border: dashed 2px  #F2C94C; padding: 1em">
                                        <b>NOTA:</b> 
                                        Para evitar uma sobrecarga hospitalar, a sua demanda (a curva 📈) deve ficar sempre abaixo da respectiva linhas tracejadas (a reta horizontal ➖).
                                        Em outras palavras, a quantidade de pessoas que precisam ser internadas por dia não deve ultrapassar o número de equipamentos disponíveis.
                                </span>
                        </div>
                </div>
        </div>
        """
        % (simulation),
        unsafe_allow_html=True,
    )

    st.plotly_chart(fig, use_container_width=True)


def try_int(possible_int):
    try:
        return int(float(possible_int))
    except Exception as e:
        return possible_int


# def genVideoTutorial():
#     st.write(
#         """<div class="base-wrapper">
#                         <span class="section-header primary-span">Antes de começar: entenda como usar!</span>
#                 </div>""",
#         unsafe_allow_html=True,
#     )
#     st.video(Link.YOUTUBE_TUTORIAL.value)


# def genStateInputSectionHeader() -> None:
#     st.write(
#         """
#         <div class="base-wrapper">
#                 <span class="section-header primary-span">Etapa 1: Selecione o seu Estado</span>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# def genMunicipalityInputSection() -> None:
#     st.write(
#         """
#         <div class="base-wrapper">
#                 <div style="display: flex; flex-direction: column">
#                         <span class="section-header primary-span">Etapa 2: Selecione seu Município ou Região SUS</span>
#                         <span>Se seu município não possui unidade de tratamento intensivo, sugerimos simular a situação da sua regional. Não recomendamos a simulação a nível estadual.</span>
#                 </div>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# def genResourceAvailabilitySection(resources: ResourceAvailability) -> None:
#     msg = f"""
#         🚨 *BOLETIM CoronaCidades:*  {resources.locality} - {datetime.now().strftime('%d/%m')}  🚨%0a%0a
#         😷 *{int(resources.cases)}* casos confirmados e *{int(resources.deaths)}* mortes%0a%0a
#         🏥 Hoje estão disponíveis *{resources.beds}* leitos e *{resources.ventilators}* ventiladores destinados à Covid %0a%0a
#         👉 _Acompanhe e simule a situação do seu município acessando o *SimulaCovid* aqui_: https://coronacidades.org/ """

#     st.write(
#         """
#         <div class="primary-bg">
#                 <div class="base-wrapper">
#                         <div class="resource-header-container">
#                                 <span class="section-header white-span">Panorama <span class="locality-name yellow-span">%s</span></span>
#                                 <a class="btn-wpp" href="whatsapp://send?text=%s" target="blank">Compartilhar no Whatsapp</a>
#                         </div>
#                         <div class="resources-wrapper">
#                                 <div class="resources-title-container">
#                                         <span class="resources-title">Progressão da Transmissão</span>
#                                 </div>
#                                 <div class="resources-container-wrapper">
#                                         <div class="resource-container">
#                                                 <span class='resource-container-value'>%i</span>
#                                                 <span class='resource-container-label'>casos confirmados</span>
#                                         </div>
#                                         <div class="resource-container">
#                                                 <span class='resource-container-value'>%i</span>
#                                                 <span class='resource-container-label'>mortes</span>
#                                         </div>
#                                 </div>
#                                 <span class="resource-font"><b>Fonte:</b> Brasil.IO atualizado diariamente com base em boletins das secretarias de saúde publicados.</span>
#                         </div>
#                         <div class="resources-wrapper">
#                                 <div class="resources-title-container">
#                                         <span class="resources-title">Capacidade hospitalar destinada à COVID</span>
#                                 </div>
#                                 <div class="resources-container-wrapper">
#                                         <div class="resource-container">
#                                                 <span class='resource-container-value'>%i</span>
#                                                 <span class='resource-container-label'>leitos</span>
#                                         </div>
#                                         <div class="resource-container">
#                                                 <span class='resource-container-value'>%i</span>
#                                                 <span class='resource-container-label'>ventiladores</span>
#                                         </div>
#                                 </div>
#                                 <span class="resource-font"><b>Fonte:</b>
#                                         DATASUS CNES, Fevereiro 2020. Assumimos que 20%% dos leitos complementares e ventiladores registrados da rede SUS e não-SUS seriam alocados para pacientes da Covid-19. Esse número poderá ser ajustado na simulação abaixo.
#                                 </span>
#                                 <div class="ambassador-container">
#                                         <span class="ambassador-question white-span bold">Esse dado está desatualizado? Você tem informações mais recentes e pode colaborar conosco?</span>
#                                         <span class="white-span">Estamos montando uma rede para manter o SimulaCovid sempre atualizado e nossas projeções serem úteis para tomada de decisão na sua cidade. Venha ser parte do nosso time de embaixadores!</span>
#                                         <a class="btn-ambassador" href="%s" target="blank">Quero ser embaixador</a>
#                                 </div>
#                         </div>
#                 </div>
#         </div>
#         """
#         % (
#             resources.locality,
#             msg,
#             resources.cases,
#             resources.deaths,
#             resources.beds,
#             resources.ventilators,
#             Link.AMBASSADOR_FORM.value,
#         ),
#         unsafe_allow_html=True,
#     )


# def genSimulationSection(
#     active_cases: int,
#     locality: str,
#     resources: ResourceAvailability,
#     worst_case: SimulatorOutput,
#     best_case: SimulatorOutput,
# ) -> None:
#     no_quarentine = (
#         "mais de 90"
#         if (worst_case.max_range_beds == -1 and worst_case.max_range_ventilators == -1)
#         else min(worst_case.max_range_beds, worst_case.max_range_ventilators)
#     )
#     date_proj = ""
#     if no_quarentine != "mais de 90":
#         proj = (datetime.now() + timedelta(days=int(no_quarentine))).strftime("%d/%m")
#         date_proj = f" *({proj})* "

#     msg = f"""
#         🚨 *BOLETIM SimulaCovid:*  {resources.locality} - {datetime.now().strftime('%d/%m')}  🚨%0a%0a
#         🏥 Considerando que {resources.locality} tem *{resources.beds}* leitos 🛏️ e *{resources.ventilators}* ventiladores ⚕ %0a%0a
#         😷 Na ausência de isolamento social, {resources.locality} poderia atingir a sua capacidade hospitalar em *{no_quarentine}* dias{date_proj}%0a%0a
#         👉 _Acompanhe e simule a situação do seu município acessando o *SimulaCovid* aqui_: https://coronacidades.org/ """

#     status_quo = genSimulatorOutput(worst_case)
#     restrictions = genSimulatorOutput(best_case)

#     st.write(
#         """
#         <div class="lightgrey-bg">
#                 <div class="base-wrapper">
#                         <div class="simulator-wrapper">
#                                 <span class="section-header primary-span">
#                                         <span  class="yellow-span">%s</span>
#                                         <br/>
#                                         Daqui a quantos dias será atingida a capacidade <span class="yellow-span">hospitalar</span>?
#                                 </span>
#                                 <br/>
#                                 <br/>
#                                 <div class="simulation-scenario-header-container">
#                                         <span class="simulator-scenario-header grey-bg">
#                                                 Sem Políticas de Restrição
#                                         </span>
#                                 </div>
#                                 %s
#                                 <br/>
#                                 <br/>
#                                 <div class="simulation-scenario-header-container">
#                                         <span class="simulator-scenario-header lightblue-bg">
#                                                 Com Medidas Restritivas (Isolamento Social)
#                                         </span>
#                                 </div>
#                                 %s
#                                 <a class="btn-wpp" href="whatsapp://send?text=%s" target="blank">Compartilhar no Whatsapp</a>
#                         </div>
#                 </div>
#         </div>
#         """
#         % (locality, status_quo, restrictions, msg),
#         unsafe_allow_html=True,
#     )


# def genActNowSection(locality, worst_case):
#     display = (
#         ""
#         if any(
#             value != -1
#             for value in [
#                 worst_case.min_range_beds,
#                 worst_case.max_range_beds,
#                 worst_case.min_range_ventilators,
#                 worst_case.max_range_ventilators,
#             ]
#         )
#         else "hide"
#     )

#     st.write(
#         """
#         <div class="primary-bg %s">
#                 <div class="base-wrapper">
#                         <div class="act-now-wrapper">
#                         <span class="section-header white-span"><span class="yellow-span">%s | </span> Você precisa agir agora </span>
#                         <span class="white-span">Para prevenir uma sobrecarga hospitalar, é preciso implementar uma estratégia de contenção. Quanto antes você agir, mais vidas consegue salvar.</span>
#                         </div>
#                 </div>
#         </div>
#         """
#         % (display, locality),
#         unsafe_allow_html=True,
#     )

# def genStrategyCard(strategy: ContainmentStrategy) -> str:
#     return """
#         <div class="scenario-card">
#                         <div class="scenario-card-header">
#                                 <span class="scenario-card-header-code %s">ESTRATÉGIA %i</span>
#                                 <div class="scenario-card-header-name-background %s">
#                                         <span class="scenario-card-header-name">%s</span>
#                                 </div>
#                         </div>
#                         <img src="%s" class="scenario-card-img"/>
#                         <span class="scenario-card-description">%s</span>
#         </div>""" % (
#         strategy.color.value,
#         strategy.code,
#         strategy.background.value,
#         strategy.name,
#         strategy.image_url,
#         strategy.description,
#     )


# def genStrategiesSection(strategies: List[ContainmentStrategy]) -> None:
#     cards = list(map(genStrategyCard, strategies))
#     cards = "".join(cards)
#     st.write(
#         """
#         <div class="primary-bg">
#                 <div class="base-wrapper">
#                         <span class="section-header white-span">E como você pode reagir?</span>
#                         <div class="scenario-cards-container">%s</div>
#                 </div>
#         </div>
#         """
#         % cards,
#         unsafe_allow_html=True,
#     )
