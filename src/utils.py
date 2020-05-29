import streamlit as st
from datetime import datetime
from datetime import timedelta
from typing import List, Dict
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


# code from: https://gist.github.com/treuille/bc4eacbb00bfc846b73eec2984869645
def cache_on_button_press(label, **cache_kwargs):
    """Function decorator to memoize function executions.

    Parameters
    ----------
    label : str
        The label for the button to display prior to running the cached funnction.
    cache_kwargs : Dict[Any, Any]
        Additional parameters (such as show_spinner) to pass into the underlying @st.cache decorator.

    Example
    -------
    This show how you could write a username/password tester:

    >>> @cache_on_button_press('Authenticate')
    ... def authenticate(username, password):
    ...     return username == "buddha" and password == "s4msara"
    ...
    ... username = st.text_input('username')
    ... password = st.text_input('password')
    ...
    ... if authenticate(username, password):
    ...     st.success('Logged in.')
    ... else:
    ...     st.error('Incorrect username or password')
    """
    internal_cache_kwargs = dict(cache_kwargs)
    internal_cache_kwargs["allow_output_mutation"] = True
    internal_cache_kwargs["show_spinner"] = False

    def function_decorator(func):
        @functools.wraps(func)
        def wrapped_func(*args, **kwargs):
            @st.cache(**internal_cache_kwargs)
            def get_cache_entry(func, args, kwargs):
                class ButtonCacheEntry:
                    def __init__(self):
                        self.evaluated = False
                        self.return_value = None

                    def evaluate(self):
                        self.evaluated = True
                        self.return_value = func(*args, **kwargs)

                return ButtonCacheEntry()

            cache_entry = get_cache_entry(func, args, kwargs)
            if not cache_entry.evaluated:
                if st.button(label):
                    cache_entry.evaluate()
                else:
                    raise st.ScriptRunner.StopException
            return cache_entry.return_value

        return wrapped_func

    return function_decorator


def fix_dates(df):

    for col in df.columns:
        if "last_updated" in col:
            df[col] = pd.to_datetime(df[col]).apply(lambda x: x.strftime("%d/%m/%Y"))
    return df


def add_all(x, all_string="Todos"):
    return [all_string] + list(x)


# TODO: melhorar essa funcao
def get_sources(data, resources, cities_sources):

    sources = dict()

    for x in resources:

        for item in ["author_number", "last_updated_number", "number"]:
            col = "_".join([item, x])

            if not col in data.columns:
                sources[col] = (
                    cities_sources[
                        cities_sources["state_id"] == data["state_id"].iloc[0]
                    ][col]
                    .drop_duplicates()
                    .fillna(0)
                    .values
                )
            else:
                sources[col] = data[col].drop_duplicates().fillna(0).values

    return sources


configs_path = os.path.join(os.path.dirname(__file__), "configs")
cities = pd.read_csv(os.path.join(configs_path, "cities_table.csv"))
states = pd.read_csv(os.path.join(configs_path, "states_table.csv"))

# In: name of the state (returns a numerical id of only the state) or the name of the state and the name of the city
# Out: the numerical id of the state of the city
def get_place_id_by_names(state_name, city_name_input="Todos"):
    state_num_id = states.query("state_name == '%s'" % state_name).values[0][-1]
    if city_name_input == "Todos":
        return state_num_id
    city_id = (
        cities.query("state_num_id == '%s'" % state_num_id)
        .query("city_name == '%s'" % city_name_input)
        .values[0][1]
    )
    return city_id


# In: id of a place (id < 100 for states, id > 100 for cities)
# Out: either a string representing the name of the state or a list contaning [state name,city name]
def get_place_names_by_id(place_id):
    if place_id <= 100:
        return states.query("state_num_id == '%s'" % place_id).values[0][2]
    else:
        data = cities.query("city_id == '%s'" % place_id).values[0]
        city_name = data[2]
        state_id = data[3]
        state_name = states.query("state_num_id == '%s'" % state_id).values[0][2]
        return [state_name, city_name]


def make_clickable(text, link):
    # target _blank to open new window
    # extract clickable text to display for your link
    return f'<a target="_blank" href="{link}">{text}</a>'


def localCSS(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def choose_place(city, region, state):
    if city == "Todos" and region == "Todos" and state == "Todos":
        return "Brasil"
    if city == "Todos" and region == "Todos":
        return state + " (Estado)" if state != "Todos" else "Brasil"
    if city == "Todos":
        return region + " (Região SUS)" if region != "Todos" else "Todas as regiões SUS"
    return city


"""View Components CentralCOVID"""


def genHeroSection(title: str, subtitle: str):
    st.write(
        f"""
        <div class="base-wrapper hero-bg">
                <a href="https://coronacidades.org/" target="blank" class="logo-link"><span class="logo-bold">corona</span><span class="logo-lighter">cidades</span></a>
                <div class="hero-wrapper">
                        <div class="hero-container">
                                <div class="hero-container-content">
                                        <span class="hero-container-product primary-span">{title}<br/>Covid</span>
                                        <span class="hero-container-subtitle primary-span">{subtitle}</span>
                                </div>
                        </div>   
                        <img class="hero-container-image" src="https://i.imgur.com/l3vuQdP.png"/>
                </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def genInputFields(locality, user_input, sources, config):

    # print("abrindo seletores")

    # @cache_on_button_press("Finalizar alterações")
    # def authenticate():
    #     return True

    authors_beds = ", ".join(sources["author_number_beds"])
    beds_update = sources["last_updated_number_beds"].max()

    authors_ventilators = ", ".join(sources["author_number_ventilators"])
    ventilators_update = sources["last_updated_number_ventilators"].max()

    if locality == "Brasil":
        authors_beds = "SUS e Embaixadores"
        authors_ventilators = "SUS e Embaixadores"

    user_input["n_beds"] = st.number_input(
        f"Número de leitos destinados aos pacientes com Covid-19 (fonte: {authors_beds}; atualizado: {beds_update})",
        0,
        None,
        int(user_input["n_beds"]),
    )

    user_input["n_ventilators"] = st.number_input(
        f"Número de ventiladores destinados aos pacientes com Covid-19 (fonte: {authors_ventilators}; atualizado: {ventilators_update}):",
        0,
        None,
        int(user_input["n_ventilators"]),
    )

    user_input["population_params"]["D"] = st.number_input(
        "Mortes confirmadas:", 0, None, int(user_input["population_params"]["D"])
    )

    user_input["population_params"]["I"] = st.number_input(
        "Casos ativos estimados:", 0, None, user_input["population_params"]["I"]
    )

    # if authenticate():
    #     # print("autenticado")
    #     return user_input

    # else:
    #     print("nao autenticado")
    #     return "ERROR"

    return user_input


def genIndicatorCard(indicator: Indicator):
    display_left = "flex"
    display_right = "flex"

    # print(indicator.left_display, indicator.right_display)

    if str(indicator.left_display) == "nan":
        display_left = "hide-bg"

    if str(indicator.right_display) == "nan":
        display_right = "hide-bg"

    return f"""<div class="indicator-card flex flex-column mr">
                        <span class="header p3">{indicator.header}</span>
                        <span class="p4">{indicator.caption}</span>
                        <span class="bold p2">{indicator.display}<span class="bold p4"> {indicator.unit}</span></span>
                        <div class="{IndicatorBackground(indicator.risk).name}-alert-bg risk-pill">
                                <span class="white-span p4 bold">{indicator.risk}</span>
                        </div>
                        <div class="flex flex-row flex-justify-space-between mt"> 
                                <div class="br {display_left} flex-column text-align-center pr">
                                        <span class="lighter">{indicator.left_label}</span>
                                        <span class="bold">{indicator.left_display}</span>
                                </div>
                                <div class=" bl flex flex-column text-align-center pl {display_right}">
                                        <span class="lighter">{indicator.right_label}</span>
                                        <span class="bold">{indicator.right_display}</span>
                                </div>
                        </div>
                </div>
        """


def genKPISection(locality: str, alert: str, indicators: Dict[str, Indicator]):
    # alert = float("nan")
    if not isinstance(alert, str):
        bg = "gray"
        caption = "Sugerimos que confira o nível de risco de seu estado. (Veja Níveis de Risco no menu ao lado)<br/>Seu município nao possui dados suficientes para calcularmos o nível de risco."

    else:
        bg = AlertBackground(alert).name
        caption = f"Risco {alert} de colapso no sistema de saúde (Veja Níveis de Risco no menu ao lado)"

    cards = list(map(genIndicatorCard, indicators.values()))
    cards = "".join(cards)
    msg = f"""
        🚨 *BOLETIM CoronaCidades:*  {locality} - {datetime.now().strftime('%d/%m')}  🚨%0a%0a
        😷 Cada contaminado infecta em média outras {indicators['rt'].display} pessoas 0a%0a
        🏥 A capacidade hospitalar será atingida entre {indicators['hospital_capacity'].display} dias %0a%0a
        🏥 A cada 10 pessoas infecadas, somente {indicators['subnotification_rate'].display} são identificadas%0a%0a
        👉 _Acompanhe e simule a situação do seu município acessando o *FarolCovid* aqui_: https://coronacidades.org/ """

    st.write(
        """<div class="alert-banner %s-alert-bg mb" style="margin-bottom: 0px;">
                <div class="base-wrapper flex flex-column" style="margin-top: 100px;">
                        <div class="flex flex-row flex-space-between flex-align-items-center">
                         <span class="white-span header p1">%s</span>
                         <a class="btn-wpp" href="whatsapp://send?text=%s" target="blank">Compartilhar no Whatsapp</a>
                         </div>
                        <span class="white-span p3">%s</span>
                        <div class="flex flex-row flex-m-column">%s</div>
                </div>
        </div>
        """
        % (bg, locality, msg, caption, cards),
        unsafe_allow_html=True,
    )


def genProductCard(product: Product):
    if product.recommendation == "Sugerido":
        badge_style = "primary-bg"
    elif product.recommendation == "Risco alto":
        badge_style = f"red-alert-bg"
    else:
        badge_style = "hide-bg"

    return f"""<div class="flex flex-column elevated pr pl product-card mt  ">
                <div class="flex flex-row">
                        <span class="p3 header bold uppercase">{product.name}</span>
                         <span class="{badge_style} ml secondary-badge">{product.recommendation}</span>
                </div>
                <span>{product.caption}</span>
                <img src="{product.image}" style="width: 200px" class="mt"/>
        </div>
        """


def genProductsSection(products: List[Product]):
    cards = list(map(genProductCard, products))
    cards = "".join(cards)

    st.write(
        f"""
        <div class="base-wrapper">
                <span class="section-header primary-span">COMO SEGUIR COM SEGURANÇA?</span>
                <div class="flex flex-row flex-space-around mt flex-m-column">{cards}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


"""View Components SimulaCovid"""


def genVideoTutorial():
    st.write(
        """<div class="base-wrapper">
                        <span class="section-header primary-span">Antes de começar: entenda como usar!</span>
                </div>""",
        unsafe_allow_html=True,
    )
    st.video(Link.YOUTUBE_TUTORIAL.value)


def genStateInputSectionHeader() -> None:
    st.write(
        """
        <div class="base-wrapper">
                <span class="section-header primary-span">Etapa 1: Selecione o seu Estado</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def genMunicipalityInputSection() -> None:
    st.write(
        """
        <div class="base-wrapper">
                <div style="display: flex; flex-direction: column"> 
                        <span class="section-header primary-span">Etapa 2: Selecione seu Município ou Região SUS</span>
                        <span>Se seu município não possui unidade de tratamento intensivo, sugerimos simular a situação da sua regional. Não recomendamos a simulação a nível estadual.</span>
                </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def genInputCustomizationSectionHeader(locality: str) -> None:
    st.write(
        """
        <div class="base-wrapper">
                <span class="section-header primary-span">Verifique os dados disponíveis <span class="yellow-span">(%s)</span></span>
                <br />
                <span>Usamos os dados do Brasil.io e DataSUS, mas é possível que eles dados estejam um pouco desatualizados. Se estiverem, é só ajustar os valores abaixo para continuar a simulação.</span>
                <br />
        </div>"""
        % locality,
        unsafe_allow_html=True,
    )


def genAmbassadorSection() -> None:
    st.write(
        """
        <div class="base-wrapper">
                <div class="ambassador-container">
                        <span class="ambassador-question bold">Você gostaria de atualizar algum dos dados acima? Você tem informações mais recentes e pode colaborar conosco?</span>
                        <span>Estamos montando uma rede para manter o SimulaCovid sempre atualizado e nossas projeções serem úteis para tomada de decisão na sua cidade. Venha ser parte do nosso time de embaixadores!</span>
                        <a class="btn-ambassador" href="%s" target="blank">Quero ser embaixador</a>
                </div>
        </div>
        """
        % Link.AMBASSADOR_FORM.value,
        unsafe_allow_html=True,
    )


def genResourceAvailabilitySection(resources: ResourceAvailability) -> None:
    msg = f"""
        🚨 *BOLETIM CoronaCidades:*  {resources.locality} - {datetime.now().strftime('%d/%m')}  🚨%0a%0a
        😷 *{int(resources.cases)}* casos confirmados e *{int(resources.deaths)}* mortes%0a%0a
        🏥 Hoje estão disponíveis *{resources.beds}* leitos e *{resources.ventilators}* ventiladores destinados à Covid %0a%0a
        👉 _Acompanhe e simule a situação do seu município acessando o *SimulaCovid* aqui_: https://coronacidades.org/ """

    st.write(
        """
        <div class="primary-bg"> 
                <div class="base-wrapper">
                        <div class="resource-header-container">
                                <span class="section-header white-span">Panorama <span class="locality-name yellow-span">%s</span></span>
                                <a class="btn-wpp" href="whatsapp://send?text=%s" target="blank">Compartilhar no Whatsapp</a>
                        </div>
                        <div class="resources-wrapper">
                                <div class="resources-title-container">
                                        <span class="resources-title">Progressão da Transmissão</span>
                                </div>
                                <div class="resources-container-wrapper">
                                        <div class="resource-container"> 
                                                <span class='resource-container-value'>%i</span>  
                                                <span class='resource-container-label'>casos confirmados</span>  
                                        </div>
                                        <div class="resource-container"> 
                                                <span class='resource-container-value'>%i</span>  
                                                <span class='resource-container-label'>mortes</span>  
                                        </div>
                                </div>
                                <span class="resource-font"><b>Fonte:</b> Brasil.IO atualizado diariamente com base em boletins das secretarias de saúde publicados.</span>
                        </div>
                        <div class="resources-wrapper">
                                <div class="resources-title-container">
                                        <span class="resources-title">Capacidade hospitalar destinada à COVID</span>
                                </div>
                                <div class="resources-container-wrapper">
                                        <div class="resource-container"> 
                                                <span class='resource-container-value'>%i</span>  
                                                <span class='resource-container-label'>leitos</span>  
                                        </div>
                                        <div class="resource-container"> 
                                                <span class='resource-container-value'>%i</span>  
                                                <span class='resource-container-label'>ventiladores</span>  
                                        </div>
                                </div>
                                <span class="resource-font"><b>Fonte:</b> 
                                        DATASUS CNES, Fevereiro 2020. Assumimos que 20%% dos leitos complementares e ventiladores registrados da rede SUS e não-SUS seriam alocados para pacientes da Covid-19. Esse número poderá ser ajustado na simulação abaixo.                             
                                </span>
                                <div class="ambassador-container">
                                        <span class="ambassador-question white-span bold">Esse dado está desatualizado? Você tem informações mais recentes e pode colaborar conosco?</span>
                                        <span class="white-span">Estamos montando uma rede para manter o SimulaCovid sempre atualizado e nossas projeções serem úteis para tomada de decisão na sua cidade. Venha ser parte do nosso time de embaixadores!</span>
                                        <a class="btn-ambassador" href="%s" target="blank">Quero ser embaixador</a>
                                </div>
                        </div>
                </div>
        </div>
        """
        % (
            resources.locality,
            msg,
            resources.cases,
            resources.deaths,
            resources.beds,
            resources.ventilators,
            Link.AMBASSADOR_FORM.value,
        ),
        unsafe_allow_html=True,
    )


def genSimulatorOutput(output: SimulatorOutput) -> str:
    bed_img = "https://i.imgur.com/27hutU0.png"
    ventilator_icon = "https://i.imgur.com/V419ZRI.png"

    has_bed_projection = output.min_range_beds != -1 and output.max_range_beds != -1
    bed_prep = "entre" if has_bed_projection else "em"

    has_ventilator_projection = (
        output.min_range_ventilators != -1 and output.max_range_ventilators != -1
    )
    ventilator_prep = "entre" if has_ventilator_projection else "em"

    if has_bed_projection:
        bed_min_range_date = (
            datetime.now() + timedelta(days=int(output.min_range_beds))
        ).strftime("%d/%m")
        bed_max_range_date = (
            datetime.now() + timedelta(days=int(output.max_range_beds))
        ).strftime("%d/%m")
        bed_projection = f"""{output.min_range_beds}
                        <span class="simulator-output-row-prediction-separator">e</span> 
                        {output.max_range_beds} """
        bed_rng = f" ({bed_min_range_date} - {bed_max_range_date}) "
    else:
        bed_projection = "mais de 90"
        bed_rng = f""

    if has_ventilator_projection:
        ventilator_min_range_date = (
            datetime.now() + timedelta(days=int(output.min_range_ventilators))
        ).strftime("%d/%m")
        ventilator_max_range_date = (
            datetime.now() + timedelta(days=int(output.max_range_ventilators))
        ).strftime("%d/%m")
        ventilator_projection = (
            '%i <span class="simulator-output-row-prediction-separator">e</span> %i'
            % (output.min_range_ventilators, output.max_range_ventilators)
        )
        ventilator_rng = (
            f" ({ventilator_min_range_date} - {ventilator_max_range_date}) "
        )
    else:
        ventilator_projection = "mais de 90"
        ventilator_rng = ""

    output = """
        <div>
                <div class="simulator-container %s">
                        <div class="simulator-output-wrapper">
                                <span class="simulator-output-timeframe">%s</span>
                                <div class="simulator-output-row">
                                        <span class="simulator-output-row-prediction-value">
                                                %s
                                        </span>  
                                </div> 
                                <span class="simulator-output-row-prediction-label">
                                        dias%s será atingida a capacidade máxima de <b>leitos</b>
                                </span>
                        </div>
                        <img src="%s" class="simulator-output-image"/>
                </div>
                <br />
                <div class="simulator-container %s">
                        <div class="simulator-output-wrapper">
                                <span class="simulator-output-timeframe">%s</span>
                                <div class="simulator-output-row">
                                        <span class="simulator-output-row-prediction-value">
                                                %s
                                        </span>  
                                </div> 
                                <span class="simulator-output-row-prediction-label">
                                        dias%s será atingida a capacidade máxima de <b>ventiladores</b>
                                </span>
                        </div>
                        <img src="%s" class="simulator-output-image"/>
                </div>
        </div>""" % (
        output.color.value,
        bed_prep,
        bed_projection,
        bed_rng,
        bed_img,
        output.color.value,
        ventilator_prep,
        ventilator_projection,
        ventilator_rng,
        ventilator_icon,
    )

    return output.strip("\n\t")


def genSimulationSection(
    active_cases: int,
    locality: str,
    resources: ResourceAvailability,
    worst_case: SimulatorOutput,
    best_case: SimulatorOutput,
) -> None:
    no_quarentine = (
        "mais de 90"
        if (worst_case.max_range_beds == -1 and worst_case.max_range_ventilators == -1)
        else min(worst_case.max_range_beds, worst_case.max_range_ventilators)
    )
    date_proj = ""
    if no_quarentine != "mais de 90":
        proj = (datetime.now() + timedelta(days=int(no_quarentine))).strftime("%d/%m")
        date_proj = f" *({proj})* "

    msg = f"""
        🚨 *BOLETIM SimulaCovid:*  {resources.locality} - {datetime.now().strftime('%d/%m')}  🚨%0a%0a
        🏥 Considerando que {resources.locality} tem *{resources.beds}* leitos 🛏️ e *{resources.ventilators}* ventiladores ⚕ %0a%0a
        😷 Na ausência de isolamento social, {resources.locality} poderia atingir a sua capacidade hospitalar em *{no_quarentine}* dias{date_proj}%0a%0a
        👉 _Acompanhe e simule a situação do seu município acessando o *SimulaCovid* aqui_: https://coronacidades.org/ """

    status_quo = genSimulatorOutput(worst_case)
    restrictions = genSimulatorOutput(best_case)

    st.write(
        """
        <div class="lightgrey-bg">
                <div class="base-wrapper">
                        <div class="simulator-wrapper">
                                <span class="section-header primary-span">
                                        <span  class="yellow-span">%s</span>
                                        <br/>
                                        Daqui a quantos dias será atingida a capacidade <span class="yellow-span">hospitalar</span>?
                                </span>
                                <br/>
                                <br/>
                                <div class="simulation-scenario-header-container">
                                        <span class="simulator-scenario-header grey-bg">
                                                Sem Políticas de Restrição
                                        </span>
                                </div>
                                %s
                                <br/>
                                <br/>
                                <div class="simulation-scenario-header-container">
                                        <span class="simulator-scenario-header lightblue-bg">
                                                Com Medidas Restritivas (Isolamento Social)
                                        </span>
                                </div>
                                %s
                                <a class="btn-wpp" href="whatsapp://send?text=%s" target="blank">Compartilhar no Whatsapp</a>
                        </div>
                </div>
        </div>
        """
        % (locality, status_quo, restrictions, msg),
        unsafe_allow_html=True,
    )


def genActNowSection(locality, worst_case):
    display = (
        ""
        if any(
            value != -1
            for value in [
                worst_case.min_range_beds,
                worst_case.max_range_beds,
                worst_case.min_range_ventilators,
                worst_case.max_range_ventilators,
            ]
        )
        else "hide"
    )

    st.write(
        """
        <div class="primary-bg %s">
                <div class="base-wrapper">
                        <div class="act-now-wrapper">
                        <span class="section-header white-span"><span class="yellow-span">%s | </span> Você precisa agir agora </span>
                        <span class="white-span">Para prevenir uma sobrecarga hospitalar, é preciso implementar uma estratégia de contenção. Quanto antes você agir, mais vidas consegue salvar.</span>
                        </div>
                </div>
        </div>
        """
        % (display, locality),
        unsafe_allow_html=True,
    )


def genStrategyCard(strategy: ContainmentStrategy) -> str:
    return """
        <div class="scenario-card">
                        <div class="scenario-card-header">
                                <span class="scenario-card-header-code %s">ESTRATÉGIA %i</span>
                                <div class="scenario-card-header-name-background %s">
                                        <span class="scenario-card-header-name">%s</span>
                                </div>
                        </div>
                        <img src="%s" class="scenario-card-img"/>
                        <span class="scenario-card-description">%s</span>
        </div>""" % (
        strategy.color.value,
        strategy.code,
        strategy.background.value,
        strategy.name,
        strategy.image_url,
        strategy.description,
    )


def genStrategiesSection(strategies: List[ContainmentStrategy]) -> None:
    cards = list(map(genStrategyCard, strategies))
    cards = "".join(cards)
    st.write(
        """
        <div class="primary-bg">
                <div class="base-wrapper">
                        <span class="section-header white-span">E como você pode reagir?</span>
                        <div class="scenario-cards-container">%s</div>
                </div>
        </div>
        """
        % cards,
        unsafe_allow_html=True,
    )


def genChartSimulationSection(simulation: SimulatorOutput, fig) -> None:

    simulation = genSimulatorOutput(simulation)
    #     sd_date = (datetime.now() + timedelta(days=int(time2sd))).strftime("%d/%m")
    #     lockdown_date = (datetime.now() + timedelta(days=int(time2lockdown))).strftime(
    #         "%d/%m"
    #     )

    #     simulation_description = ""
    #     if time2lockdown <= time2sd:

    #         if time2lockdown == 0:
    #             simulation_description = (
    #                 f"Começando a quarentena <b>hoje</b> ({lockdown_date}):"
    #             )
    #         else:
    #             simulation_description = f"Começando a quarentena em <b>{time2lockdown}</b> dias ({lockdown_date}):"
    #     else:  # lockdown after social distancing
    #         if time2sd == 0:
    #             simulation_description = f"Começando o isolamento social <b>hoje</b>  ({sd_date}) e a quarentena em <b>{time2lockdown}</b> dias ({lockdown_date}):"
    #         else:
    #             simulation_description = f"Começando o isolamento social em <b>{time2sd}</b> dias ({sd_date}) e a quarentena em <b>{time2lockdown}</b> dias ({lockdown_date}):"

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

    st.plotly_chart(fig)


def genFooter() -> None:
    st.write(
        """
        <div class="magenta-bg">
                <div class="base-wrapper">
                        <div class="logo-wrapper">
                                <span>A presente ferramenta, voluntária, parte de estudos referenciados já publicados e considera os dados de saúde pública dos municípios brasileiros disponibilizados no DataSus. O repositório do projeto pode ser acessado no nosso <a class="github-link" href="https://github.com/ImpulsoGov/simulacovid">Github</a></span>
                                <br/>
                                <span>Os cenários projetados são meramente indicativos e dependem de variáveis que aqui não podem ser consideradas. Trata-se de mera contribuição à elaboração de cenários por parte dos municípios e não configura qualquer obrigação ou responsabilidade perante as decisões efetivadas. Saiba mais em nossa metodologia.</span>
                                <br/>
                                <span>Estamos em constante desenvolvimento e queremos ouvir sua opinião sobre a ferramenta - caso tenha sugestões ou comentários, entre em contato via o chat ao lado. Caso seja gestor público e necessite de apoio para preparo de seu município, acesse a Checklist e confira o site do CoronaCidades.</span>
                                <br/>
                                <img class="logo-img" src="%s"/>
                                <div class="logo-section">
                                        <img class="logo-img" src="%s"/>
                                        <img class="logo-img" src="%s"/>
                                </div>
                        </div>'
                </div>
        </div>"""
        % (Logo.IMPULSO.value, Logo.CORONACIDADES.value, Logo.ARAPYAU.value),
        unsafe_allow_html=True,
    )


def genWhatsappButton() -> None:
    msg = f"Olá Equipe Coronacidades. Vocês podem me ajuda com uma dúvida?"
    phone = "+5511964373097"
    url = "whatsapp://send?text={}&phone=${}".format(msg, phone)
    st.write(
        """ 
         <a href="%s" class="float" target="_blank" id="messenger">
                <i class="material-icons">question_answer</i>
                <p class="float-header">Dúvidas?</p></a>
        """
        % url,
        unsafe_allow_html=True,
    )


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
