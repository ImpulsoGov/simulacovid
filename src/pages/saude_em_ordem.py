import streamlit as st
import amplitude
import utils
import loader
import bisect
import random
import plotly as plt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import math
import os
import pandas as pd
import session
import urllib.parse

DO_IT_BY_RANGE = (
    True  # DEFINES IF WE SHOULD RUN OUR CODE BY METHOD 1 (TRUE) OR 2 (FALSE)
)
# METHOD 1 IS DIVIDING THE RANGE OF VALUES IN 4 EQUAL PARTS IN SCORE VALUE
# METHOD 2 IS DIVIDING OUR ACTIVITIES IN GROUPS OF ROUGHLY EQUAL SIZE AFTER RANKING THEM

# INITIAL DATA PROCESSING
def get_score_groups(config, session_state, slider_value):
    """ Takes our data and splits it into 4 sectors for use by our diagram generator """
    # uf_num = utils.get_place_id_by_names(session_state.state)

    if (
        session_state.city_name != "Todos"
        or session_state.health_region_name != "Todos"
    ):
        endpoint = "health_region"
        col = "health_region_id"
        value = session_state.health_region_id
        place_name = session_state.health_region_name + " (Região de Saúde)"

    else:
        endpoint = "state"
        col = "state_num_id"
        value = session_state.state_num_id
        place_name = session_state.state_name + " (Estado)"

    economic_data = loader.read_data(
        "br",
        config,
        config["br"]["api"]["endpoints"]["safereopen"]["economic_data"][endpoint],
    ).query(f"{col} == {value}")

    CNAE_sectors = loader.read_data(
        "br", config, config["br"]["api"]["endpoints"]["safereopen"]["cnae_sectors"]
    )
    CNAE_sectors = dict(zip(CNAE_sectors.cnae, CNAE_sectors.activity))

    economic_data["activity_name"] = economic_data.apply(
        lambda row: CNAE_sectors[row["cnae"]], axis=1
    )
    return (
        gen_sorted_sectors(economic_data, slider_value, DO_IT_BY_RANGE,),
        economic_data,
        place_name,
    )


def gen_sorted_sectors(sectors_data, slider_value, by_range=True):
    """ Cleans the data and separates in those 4 groups for later use by the table generator """
    column_name = "cd_id_" + "%02d" % (int(slider_value / 10))
    kept_columns = [
        "cnae",
        "n_employee",
        "security_index",
        "total_wage_bill",
        "sector",
        column_name,
        "activity_name",
    ]
    data_for_objects = sectors_data[kept_columns]
    data_for_objects = data_for_objects.rename(columns={column_name: "score"})
    sectors = data_for_objects.to_dict(orient="records")
    sectors.sort(key=lambda x: x["score"])
    for i in range(len(sectors)):
        sectors[i]["index"] = len(sectors) - i
    if by_range:
        sector_groups = chunks_by_range(sectors, "score", 4)
    else:
        sector_groups = list(chunks(sectors, 4))
    return sector_groups


def chunks_by_range(target_list, key, n):
    """ Divides a list of dictionaries by a given key through the method 1 group division method"""
    # For use in a list of dicts and to sort them by a specific key
    split_indexes = range_separators_indexes(
        [element[key] for element in target_list], n
    )
    chunks = []
    last = 0
    for i in range(n - 1):
        chunks.append(target_list[last : split_indexes[i]])
        last = split_indexes[i]
    chunks.append(target_list[last::])
    return chunks


def range_separators_indexes(values, n):
    """ Given a list of values separates them into n chunks by the method 1 and returns the index of cutting"""
    # Values must be ordered from lowest to highest
    separations = [
        (((values[-1] - values[0]) / (n)) * (order + 1)) + values[0]
        for order in range(n - 1)
    ]
    return [
        bisect.bisect_right(values, separationvalue) for separationvalue in separations
    ]


def chunks(l, n):
    """
    Yields n sequential chunks of l. Used for our sector splitting protocol in method2
    """
    # Values should be sorted
    d, r = divmod(len(l), n)
    for i in range(n):
        si = (d + 1) * (i if i < r else r) + d * (0 if i < r else i - r)
        yield l[si : si + (d + 1 if i < r else d)]


# SEÇÃO DE INTRODUÇÃO

def gen_intro(alert):
    if alert == "baixo":
        st.write(
            """
        <div class="base-wrapper">
                <div class="section-header primary-span">VEJA OS SETORES MAIS SEGUROS PARA REABRIR</div><br>
                <div class="ambassador-question"><b>Legal, seu município/regional/estado está em risco <span style="color:#02B529;">BAIXO</span>! Isso significa que já é adequado pensar em retomar as atividades econômicas gradualmente.</b> Nós compilamos aqui dados econômicos do seu estado para retomada segura de atividades econômicas, ordenadas com critérios objetivos.</div>
        </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.write(
            """
        <div class="base-wrapper">
                <div class="section-header primary-span">VEJA OS SETORES MAIS SEGUROS PARA REABRIR</div><br>
                <div class="ambassador-question"><b>Opa, seu município/regional/estado ainda não está verde! Isso significa que <span style="color:#dd2c00;">não é o momento</span> de retomar as atividades econômicas.</b> No entanto, para fins de planejamento a ser implementado quando a doença for controlada, compilamos aqui dados econômicos do seu estado para retomada segura de atividades econômicas, ordenadas com critérios objetivos.</div>
        </div>""",
            unsafe_allow_html=True,
        )


def gen_illustrative_plot(sectors_data, session_state, place_name):
    """ Generates our illustrative sector diagram Version saude v2 """
    text = f""" 
    <div class="saude-alert-banner saude-blue-bg mb" style="margin-bottom: 0px;">
        <div class="base-wrapper flex flex-column" style="margin-top: 0px;">
            <div class="flex flex-row flex-space-between flex-align-items-center">
                <span class="white-span header p1"> Ordem de Retomada dos Setores | {place_name}</span>
            </div>
            <span class="white-span p3">Sugerimos uma retomada <b>em fases</b>, a começar pelos <b>setores mais seguros</b> e com <b>maior contribuição econômica.</b></span>
            <div class="flex flex-row flex-m-column">"""
    names_in_order = list(reversed(["d", "c", "b", "a"]))
    for index, sector_dict in enumerate(reversed(sectors_data)):
        text += gen_sector_plot_card(names_in_order[index], sector_dict, size_sectors=3)
    text += """
            </div>
        </div>
        <div class="saude-white-banner-pt0"></div>
    </div>
    <div class="saude-white-banner-pt2">
        <div class="base-wrapper flex flex-column" style="margin-top: 0px;">
            <div class="saude-banner-arrow-body"></div>
            <div class="saude-banner-arrow-tip">
                <i class="saude-arrow right"></i>
            </div>
            <div class="saude-banner-button high-security">Seguro</div>
            <div class="saude-banner-button high-economy">Forte</div>
            <div class="saude-banner-desc">
                <b>Segurança Sanitária</b> mede o risco de exposição à Covid-19 dos trabalhadores de cada atividade econômica.
            </div>
            <div class="saude-banner-desc">
                <b>Contribuição Econômica</b> é medida da massa salarial dos setores formais e informais de cada atividade econômica.<br>(Veja mais em Metodologia)
            </div>
            <div class="saude-banner-button low-security">Inseguro</div>
            <div class="saude-banner-button low-economy">Fraca</div>
        </div>
    </div>"""
    text += gen_slider_header()
    st.write(text, unsafe_allow_html=True)
    # Invert the order
    st.write(
        f"""<iframe src="resources/saude-inverter.html?obj1=Caso queira, altere abaixo o peso dado à Segurança Sanitária&obj2=Ordem de Retomada dos Setores |" height="0" width="0"></iframe>""",
        unsafe_allow_html=True,
    )


def gen_sector_plot_card(sector_name, sector_data, size_sectors=5):
    """ Generates One specific card from the sector diagram version saude v2"""
    titles = {"a": "Fase 1 ✅", "b": "Fase 2 🙌", "c": "Fase 3 ‼", "d": "Fase 4 ⚠"}
    redirect_id_conversion = {"a": 3, "b": 2, "c": 1, "d": 0}
    redirect_id = "saude-table-" + str(redirect_id_conversion[sector_name])
    top_n_sectors = sector_data[-size_sectors::]
    size_rest = max(0, len(sector_data) - size_sectors)
    continuation_text = f"<b>+ {size_rest} setor{['','es'][int(size_rest >= 2)]} do grupo<br> <a href='#{redirect_id}' style='color:#00003d;'>(clique aqui para acessar)</a></b>"
    # The last 5 are the best
    item_list = "<br>".join(["- " + i["activity_name"] for i in top_n_sectors])
    average_wage = int(
        sum([float(i["total_wage_bill"]) for i in top_n_sectors]) / size_sectors
    )
    num_people = sum([int(i["n_employee"]) for i in top_n_sectors])
    text = f"""
    <div class="saude-indicator-card flex flex-column mr" style="z-index:1;display:inline-block;position:relative;">
        <span class="saude-card-header-v2">{titles[sector_name]}</span>
        <span class="saude-card-list-v2">
            {item_list}
        </span>
        <div class="flex flex-row flex-justify-space-between mt" style="width:250px;">
        </div>
        <div class="saude-card-redirect">
            {continuation_text}
        </div>
        <div class="saude-card-display-text-v2 sdcardtext-left">
                <span class="lighter">Massa Salarial Média:<br></span>
                <span class="bold">R$ {convert_money(average_wage)}</span>
        </div>
        <div class="saude-card-display-text-v2 sdcardtext-right">
                <span class="lighter">Número de Trabalhadores:<br></span>
                <span class="bold">{convert_money(num_people)}</span>
        </div>
    </div>"""
    return text


def convert_money(money):
    """ Can be used later to make money look like whatever we want, but a of
        now just adding the decimal separator should be enough
    """
    return f"{int(money):,}".replace(",", ".")


# SEÇÃO DE SELEÇÃO DE PESOS
def gen_slider(session_state):
    """ Generates the weight slider we see after the initial sector diagram and saves it to session_state"""
    radio_label = "Caso queira, altere abaixo o peso dado à Segurança Sanitária:"
    # Code in order to horizontalize the radio buttons
    radio_horizontalization_html = utils.get_radio_horizontalization_html(radio_label)
    session_state.saude_ordem_data["slider_value"] = st.radio(
        radio_label, [70, 80, 90, 100]
    )
    # print("VALOR SELECIONADO:", session_state.saude_ordem_data["slider_value"])
    st.write(
        f"""
        <div class="base-wrapper">
            {radio_horizontalization_html}
            <div class="saude-slider-value-display"><b>Peso selecionado (Segurança): {session_state.saude_ordem_data["slider_value"]}%</b>&nbsp;&nbsp;|  &nbsp;Peso restante para Economia: {100 - session_state.saude_ordem_data["slider_value"]}%</div>
        </div>""",
        unsafe_allow_html=True,
    )

    # Amplitude: Get user info
    user_analytics = amplitude.Amplitude_user()
    user_analytics.gen_user(utils.get_server_session())
    user_analytics.safe_log_event(
        "chose saude_slider_value",
        session_state,
        event_args={"slider_value": session_state.saude_ordem_data["slider_value"]},
    )
    # st.write(radio_horizontalization_html,unsafe_allow_html=True)


def gen_slider_header():
    return f"""<div class="base-wrapper">
            <div class="saude-slider-wrapper">
                <span class="section-header primary-span">ESCOLHA O PESO PARA A SEGURANÇA SANITÁRIA</span><p>
                <span class="ambassador-question" style="width:80%;max-width:1000px;"><br><b>O peso determina em qual fase classificamos cada setor econômico.</b> O peso padrão utilizado é de <b>70% para Segurança Sanitária e 30% para Contribuição Econômica</b> - a partir desse valor você pode atribuir mais peso para Segurança (mais detalhes na Metodologia).
                Este parâmetro pode ser alterado abaixo; entre em contato conosco para mais detalhes.</span><p>
            </div>
        </div>"""


# SEÇÃO DE DETALHES (INCLUDES THE DETAILED PLOT AND THE FULL DATA DOWNLOAD BUTTON)
def gen_detailed_vision(economic_data, session_state, config):
    """ Uses session_state to decided wheter to hide or show the plot """
    st.write(
        f"""
        <div class="base-wrapper">
            <span style="width: 80%; max-width: 1000px; margin-top: -50px;">
            <i><b>Clique em "Visão Detalhada" para ver o gráfico completo com todas as informações.</b></i>
            </span><br>""",
        unsafe_allow_html=True,
    )
    if st.button(
        "Visão Detalhada"
    ):  
        # If the button is clicked just alternate the opened flag and plot it
        
        # Amplitude: Get user info
        user_analytics = amplitude.Amplitude_user()
        user_analytics.gen_user(utils.get_server_session())
        user_analytics.safe_log_event(
            "picked saude_em_ordem_detailed_view",
            session_state,
            event_args={
                "state": session_state.state_name,
                "city": session_state.city_name,
            },
        )
        session_state.saude_ordem_data[
            "opened_detailed_view"
        ] = not session_state.saude_ordem_data["opened_detailed_view"]
        if session_state.saude_ordem_data["opened_detailed_view"] is True:
            display_detailed_plot(economic_data, session_state)
    else:  # If the button is not clicked plot it as well but do not alter the flag
        if session_state.saude_ordem_data["opened_detailed_view"] is True:
            display_detailed_plot(economic_data, session_state)

    utils.stylizeButton(
        name="Visão Detalhada", 
        style_string="""border: 1px solid var(--main-white);box-sizing: border-box;border-radius: 15px; width: auto;padding: 0.5em;text-transform: uppercase;font-family: var(--main-header-font-family);color: var(--main-white);background-color: var(--main-primary);font-weight: bold;text-align: center;text-decoration: none;font-size: 18px;animation-name: fadein;animation-duration: 3s;margin-top: 1em;""", 
        session_state=session_state)


def get_clean_data(in_econ_data):
    cols = in_econ_data.columns.tolist()
    cols.insert(2, "activity_name")
    cols = cols[:-1]
    economic_data = in_econ_data[cols]
    to_drop_columns = [
        i
        for i in list(economic_data.columns)
        if ("cd_id" in i and (i.split("_")[-1] not in ["07", "08", "09", "10"]))
    ]
    economic_data = economic_data.drop(to_drop_columns, axis=1)
    return economic_data


def convert_dataframe_to_html(df, name="dados"):
    uri = urllib.parse.quote(df.to_csv(index=False))
    file_name = "saude_em_ordem_" + name.replace(" ", "_") + ".csv"
    return f'<a href="data:application/octet-stream,{uri}" download="{file_name}" class="btn-ambassador">Baixar Dados Completos</a>'


def display_detailed_plot(economic_data, session_state):
    fig = plot_cnae(
        economic_data, session_state.saude_ordem_data["slider_value"], DO_IT_BY_RANGE,
    )
    st.write(
        """
        <div class="base-wrapper">
            <span class="ambassador-question" style="width: 80%; max-width: 1000px;">
            <b>Passe o mouse sobre cada bolinha para ver todos os detalhes daquela atividade econômica.</b><br>
            Se você está no celular é só clicar na bolinha. Além disso talvez seja necessário rolar a tela para ver o gráfico inteiro.
            </span>
        </div>""",
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_cnae(economic_data, slider_value, by_range=True):
    """ Will generate the colored plot seen in the detailed view section """
    fig = go.Figure()
    column_name = "cd_id_" + "%02d" % (int(slider_value / 10))

    numpy_econ_version = economic_data[
        ["activity_name", column_name, "total_wage_bill"]
    ].to_numpy()

    fig.add_trace(
        go.Scatter(
            x=economic_data["total_wage_bill"],
            y=economic_data["security_index"],
            name="Atividade Econômica",
            mode="markers",
            customdata=numpy_econ_version,
            text=economic_data["sector"],
            hovertemplate="<b>%{customdata[0]}</b><br><br>"
            + "Pontuação: %{customdata[1]}<br>"
            + "índice de Segurança: %{y:,.2f}<br>"
            + "Massa Salarial: R$%{customdata[2]:.0}<br>"
            + "Setor: %{text}"
            + "<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_type="log",
        xaxis_title="Contribuição Econômica",
        yaxis_title="Índice de Segurança",
        font=dict(family="Oswald", size=12, color="#000000"),
    )
    wage_range = [
        int(np.amin(economic_data["total_wage_bill"].values)),
        int(np.amax(economic_data["total_wage_bill"].values)),
    ]
    safety_range = [
        int(np.amin(economic_data["security_index"].values)),
        int(np.amax(economic_data["security_index"].values)),
    ]
    sorted_score = sorted(economic_data[column_name])
    if by_range:
        score_group_limits = (
            [0]
            + [
                sorted_score[index]
                for index in range_separators_indexes(sorted_score, 4)
            ]
            + [200]
        )
    else:
        score_group_limits = (
            [0] + [sorted_score[i] for i in chunk_indexes(len(sorted_score), 4)] + [200]
        )
    gen_isoscore_lines(fig, score_group_limits, wage_range, slider_value / 100)
    fig.update_layout(  # The 0.85 and 1.15 factors are to add some margin to the plot
        xaxis=dict(
            range=[
                math.log(wage_range[0] * 0.85, 10),
                math.log(wage_range[1] * 1.15, 10),
            ]
        ),
        yaxis=dict(
            range=[safety_range[0] * 0.95, safety_range[1] * 1.05]
        ),  # Same reason for 0.95 and 1.05
        height=540,
        width=900,
    )
    return fig


def chunk_indexes(size, n):
    """
    Similar to the chunks() method but it gives us the splitting indexes
    """
    last = 0
    while n > 1:
        new_index = last + math.ceil(size / n)
        yield new_index
        size = size - math.ceil(size / n)
        last = new_index
        n = n - 1


def gen_isoscore_lines(fig, score_parts, wage_range, weight):
    """
    Goes through each value defining a iso-score line and draws it on the plot with a colored area.
    Must also include the minimum limit and the maximum limit in score_parts if we want 4 shaded areas we include 5 lines
    and the plot will be colored between line 1 and 2, 2 and 3, 3 and 4 and 4 and 5 totalling 4 parts
    
    """
    # x is wage_range
    x_data = np.logspace(
        np.log(wage_range[0] * 0.85), np.log(wage_range[1] * 1.15), 50, base=np.e
    )
    names = ["Nan", "Fase 4", "Fase 3", "Fase 2", "Fase 1"]
    area_colors = [
        "#FFFFFF",
        "rgba(252,40,3,0.2)",
        "rgba(252,190,3,0.2)",
        "rgba(227,252,3,0.2)",
        "rgba(3,252,23,0.2)",
    ]
    legend_visibility = [False, True, True, True, True]
    for index, score in enumerate(score_parts):
        y_data = np.power(
            np.divide(score, np.power(np.log(x_data), 1 - weight)), 1 / weight
        )
        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=y_data,
                fill="tonexty",
                mode="none",
                name=names[index],
                line_color=area_colors[index],
                fillcolor=area_colors[index],
                visible=True,
                showlegend=legend_visibility[index],
            )
        )


# SEÇÃO DE TABELAS DE SETORES
def gen_sector_tables(
    session_state,
    score_groups,
    config,
    default_size=5,
    download=False,
    econ_data=None,
    download_name="dados",
):
    """
    Major function that will generate all the tables from all the sectors.
    Uses session_state to decided if the table is open or closed
    """
    text = ""
    if download:
        clean_econ_data = get_clean_data(econ_data)
        download_text = convert_dataframe_to_html(clean_econ_data, name=download_name)
    else:
        # download_text = f"""
        # <a href="" download="dados_estado.csv" class="btn-ambassador disabled">
        # Baixar dados (Desativado)
        # </a>"""
        download_text = " "
    st.write(
        f"""
        <div class="base-wrapper">
            <span class="section-header primary-span">TABELAS DE CONTRIBUIÇÃO DOS SETORES</span><p><br>
            <span class="ambassador-question">Abaixo você pode conferir todos os setores de cada grupo de apresentados, ordenados pelo <b>índice de priorização de reabertura Saúde em Ordem.</b></span>
            <div><br>
            <div class="saude-download-clean-data-button-div">{download_text}
            </div>""",
        unsafe_allow_html=True,
    )

    for table_index in reversed(range(4)):
        number = str(4 - table_index)
        # We create it all under a button but the table will be shown either way
        # The button is merely to alternate the state between open and closed
        if st.button("Mostrar/Ocultar mais da Fase " + number):
            session_state.saude_ordem_data["opened_tables"][
                table_index
            ] = not session_state.saude_ordem_data["opened_tables"][table_index]
            gen_single_table(session_state, score_groups, table_index, default_size)
        else:
            gen_single_table(session_state, score_groups, table_index, default_size)

        utils.stylizeButton(
            name="Mostrar/Ocultar mais da Fase " + number, 
            style_string="""border: 1px solid var(--main-white);box-sizing: border-box;border-radius: 15px; width: auto;padding: 0.5em;text-transform: uppercase;font-family: var(--main-header-font-family);color: var(--main-white);background-color: var(--main-primary);font-weight: bold;text-align: center;text-decoration: none;font-size: 18px;animation-name: fadein;animation-duration: 3s;margin-top: 1em;""", 
            session_state=session_state,
        )


def gen_single_table(session_state, score_groups, data_index, n=5):
    """ Generates an entire table for one sector given the data we have and the index of such sector from D to A """
    text = ""  # Our HTML will be stored here
    # Constants
    titles = ["Fase 4 ⚠", "Fase 3 ‼", "Fase 2 🙌", "Fase 1 ✅"]
    safety_statuses = [
        [["Inseguro", "#FF5F6B"], ["Fraco", "#FF5F6B"]],
        [["Inseguro", "#FF5F6B"], ["Forte", "#02BC17"]],
        [["Seguro", "#02BC17"], ["Fraco", "#FF5F6B"]],
        [["Seguro", "#02BC17"], ["Forte", "#02BC17"]],
    ]
    safety_display = safety_statuses[data_index]
    # If the user chose to open the table we extende the amount of rows to the full size of the group
    if session_state.saude_ordem_data["opened_tables"][data_index] is True:
        n = len(score_groups[data_index])
    else:
        n = min(n, len(score_groups[data_index]))  # goes to a max of n
    table_id = "saude-table-" + str(data_index)

    # print("Quantos itens selecionamos?", n)
    working_data = list(reversed(score_groups[data_index][-n:]))
    proportion = (
        str((n + 1) * 5) + "vw"
    )  # The height of our table so we can draw the lines
    total_workers = sum([sec_data["n_employee"] for sec_data in working_data])
    total_wages = sum([sec_data["total_wage_bill"] for sec_data in working_data])
    text += f"""<div class="saude-table" id="{table_id}">
        <div class="saude-table-title-box">
            <div class="saude-table-title">{titles[data_index]}</div>
            <div class="saude-table-title-security-label">Segurança Sanitária</div>
            <div class="saude-table-title-economy-label">Contribuição Econômica</div>
            <div class="saude-table-title-button tbsecurity" style="background: {safety_display[0][1]};">{safety_display[0][0]}</div>
            <div class="saude-table-title-button tbeconomy" style="background: {safety_display[1][1]};">{safety_display[1][0]}</div>
        </div>
        <div class="saude-table-head-box">
            <div class="saude-table-line tl0" style="height: {proportion};"></div>
            <div class="saude-table-line tl1" style="height: {proportion};"></div>
            <div class="saude-table-line tl2" style="height: {proportion};"></div>
            <div class="saude-table-line tl3" style="height: {proportion};"></div>
            <div class="saude-table-field tt0">Ranking</div>
            <div class="saude-table-field tt1">Nome do setor</div>
            <div class="saude-table-field tt2">Índice de Segurança Sanitária</div>
            <div class="saude-table-field tt3">N°de Trabalhadores</div>
            <div class="saude-table-field tt4">Massa Salarial</div>
        </div>"""
    for index, sector_data in enumerate(working_data):
        text += gen_sector_table_row(sector_data, index)
    text += f"""<div class="saude-table-total-box">
            <div class="saude-table-field te1">Total</div>
            <div class="saude-table-field te3">{convert_money(total_workers)}</div>
            <div class="saude-table-field te4">R$ {convert_money(total_wages)}</div>
        </div>
        <div class="saude-table-endspacer">
        </div>
    </div>"""
    st.write(text, unsafe_allow_html=True)
    return text


def gen_sector_table_row(sector_data, row_index):
    """ Generates a row of a table given the necessary information coming from a sector data row """
    return f"""<div class="saude-table-row {["tlblue","tlwhite"][row_index % 2]}">
            <div class="saude-table-field tf0">{sector_data["index"]}</div>
            <div class="saude-table-field tf1">{sector_data["activity_name"]}</div>
            <div class="saude-table-field tf2">{"%0.2f"%sector_data["security_index"]}</div>
            <div class="saude-table-field tf3">{convert_money(sector_data["n_employee"])}</div>
            <div class="saude-table-field tf4">R$ {convert_money(sector_data["total_wage_bill"])}</div>
        </div>"""


# SEÇÃO DE PROTOCOLOS
def gen_protocols_section():
    st.write(
        """
    <div class="base-wrapper">
        <span class="section-header primary-span">
            DIRETRIZES PARA A ELABORAÇÃO DE PROTOCOLOS DE REABERTURA
        </span><br><br>
        <span class="ambassador-question"><br>
            <b>Eliminação</b> – contempla a transferência para o trabalho remoto, ou seja, elimina riscos ocupacionais. Mesmo que a residência do funcionário não tenha a infraestrutura necessária, a transferência de computadores ou melhorias de acesso à internet são medidas possíveis e de baixo custo, com fácil implementação.
            <br><br>
            <b>Substituição</b>  – consiste em substituir riscos onde eles são inevitáveis, por um de menor magnitude. Vale assinalar os times que são ou não essenciais no trabalho presencial e segmentar a força de trabalho, mantendo somente o mínimo necessário de operação presencial e reduzindo o contato próximo entre times diferentes. 
            <br><br>
            <b>Controles de engenharia</b>  – fala de aspectos estruturais do ambiente de trabalho. No caso do coronavírus, podem ser citados como exemplos o controle de ventilação e purificação de ar, reduzindo o risco da fonte e não no nível individual. São fatores altamente ligados ao contexto, seja da atividade, seja do espaço físico onde ocorrem.
            <br><br>
            <b>Controles administrativos</b>  – consiste nos controles de fluxo e quantidade de pessoas no ambiente de trabalho (de-densificação do ambiente) e sobre protocolos e regras a serem seguidos, como periodicidade e métodos de limpeza, montagem de plantões e/ou escala, organização de filas para elevadores e uso de áreas comuns, proibição de reuniões presenciais, reorganização das estações de trabalho para aumentar distância entre pessoas para 2m ou mais, etc. 
            <br><br>
            <b>EPIs</b>  – definição de qual é o EPI necessário para cada função, levando em conta o risco de cada atividade e também o ambiente. Trabalhos mais fisicamente exaustivos geralmente requerem troca de EPI mais constante ou especificações diferentes de outras atividades. É preciso garantir o correto uso desses equipamentos. No caso de máscaras simples, convém que a empresa distribua para os funcionários, garantindo certas especificações. Por exemplo, 
            <br><br>
            <i>OBSERVAÇÃO:</i> quanto mais alto na hierarquia, menos capacidade de supervisão e execução é exigida do empregador. Por isso, a primeira pergunta é sempre “quem pode ficar em casa?”. Treinar supervisores, garantir alinhamento institucional e cumprimento impecável de protocolos, etc. tem um custo e são medidas de difícil controle.
            <br><br>
            <b>Materiais de Referência:</b><br>
            <a href="http://www.pe.sesi.org.br/Documents/Guia_SESI_de_prevencao_2805_2%20(1).pdf" style="color: blue;">[1] Guia SESI de prevenção da Covid-19 nas empresas (atualizado em 26/5/2020).</a><br>
            <a href="https://www.osha.gov/shpguidelines/hazard-prevention.html" style="color: blue;">[2] Recommended Practices for Safety and Health Programs - United States Department of Labor</a></br>
            <br><br>
        </span>
        <figure>
            <img class="saude-reopening-protocol-img-1" alt="Fonte: HIERARCHY OF CONTROLS -The National Institute for Occupational Safety and Health (NIOSH); disponível em https://www.cdc.gov/niosh/topics/hierarchy/default.html" src="https://i.imgur.com/St9fAMB.png"><br>
            <figcaption><i>Fonte: HIERARCHY OF CONTROLS -The National Institute for Occupational Safety and Health (NIOSH); disponível em https://www.cdc.gov/niosh/topics/hierarchy/default.html</i></figcaption>
        </figure>
    </div>""",
        unsafe_allow_html=True,
    )


def gen_partners_section():
    st.write(
        """
    <div class="base-wrapper">
        <span class="section-header primary-span">
            APOIO TÉCNICO
        </span><br><br>
        <figure>
            <img class="saude-reopening-protocol-img-1" alt="Vital Strategies - Resolve to Save Lives" src="https://i.imgur.com/iY7X2Qb.jpg"><br>
        </figure>
    </div>""",
        unsafe_allow_html=True,
    )


# MAIN
def main(user_input, indicators, data, config, session_state):
    # TODO:o que isso faz??
    st.write(
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        unsafe_allow_html=True,
    )
    if (
        session_state.saude_ordem_data == None
    ):  # If not loaded, load the data we are going to use in the user database
        session_state.saude_ordem_data = {
            "slider_value": 70,
            "opened_tables": [True, True, True, True],
            "opened_detailed_view": False,
        }

    utils.genHeroSection(
        title1="Saúde", 
        title2="Em Ordem",
        subtitle="Contribuindo para uma retomada segura da economia.", 
        logo="https://i.imgur.com/FiNi6fy.png",
        header=False
    )
    
    gen_intro(alert=data["overall_alert"].values[0])
    gen_slider(session_state)
    score_groups, economic_data, place_name = get_score_groups(
        config, session_state, session_state.saude_ordem_data["slider_value"]
    )

    gen_illustrative_plot(score_groups, session_state, place_name)
    gen_detailed_vision(economic_data, session_state, config)
    gen_sector_tables(
        session_state,
        score_groups,
        config,
        default_size=5,
        download=True,
        econ_data=economic_data,
        download_name=place_name,
    )
    gen_protocols_section()
    gen_partners_section()
