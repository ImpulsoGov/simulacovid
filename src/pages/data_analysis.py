import streamlit as st
import loader
import yaml
import plotly.graph_objs as go
from plotly.io import to_html
import plotly.io as pio
import numpy as np
import pandas as pd
import utils
import amplitude


def _get_rolling_amount(grp, time, data_col="last_updated", col_to_roll="new_deaths"):
    return grp.rolling(time, min_periods=1, on=data_col)[col_to_roll].mean()


def _df_to_plotly(df):
    return {"z": df.values.tolist(), "x": df.columns.tolist(), "y": df.index.tolist()}


def _generate_hovertext(df_to_plotly, deaths_per_cases=False):
    color_value_label = "Percentual do máximo"
    if deaths_per_cases:
        color_value_label = "Mortes por casos"
    hovertext = list()
    for yi, yy in enumerate(df_to_plotly["y"]):
        hovertext.append(list())
        for xi, xx in enumerate(df_to_plotly["x"]):
            hovertext[-1].append(
                "<b>{}</b><br>Data: {}<br>{}: {}".format(
                    yy,
                    str(xx)[:10],
                    color_value_label,
                    round(df_to_plotly["z"][yi][xi], 2),
                )
            )

    return hovertext


def plot_heatmap(
    df,
    place_type,
    legend,
    title=None,
    group=None,
    city_name=None,
    deaths_per_cases=False,
):
    if place_type == "state_id" or place_type == "city_name":
        col_date = "last_updated"
        col_deaths = "deaths"
        col_actual_data = "rolling_deaths_new"
        if deaths_per_cases:
            col_deaths = "deaths_per_cases"
            col_actual_data = "deaths_per_cases"

    if place_type == "country_pt":
        col_date = "date"
        col_deaths = "total_deaths"
        col_actual_data = "rolling_deaths_new"
    pivot = (
        df.reset_index()
        .pivot(index=place_type, columns=col_date, values=col_actual_data)
        .fillna(0)
    )
    if not deaths_per_cases:
        pivot = pivot.apply(lambda x: x / x.max(), axis=1)

    pivot = pivot.dropna(how="all")
    # remove days with all states zero
    pivot = pivot.loc[:, (pivot != 0).any(axis=0)]

    # TODO: analisar remoção de mortes nos locais
    pivot = pivot.applymap(lambda x: 0 if x < 0 else x)
    # entender o que acontece aqui
    states_total_deaths = (
        df.groupby(place_type)[col_deaths]
        .max()
        .loc[pivot.index]
        .sort_values(ascending=False)
    )
    if deaths_per_cases:
        states_total_deaths = df.reset_index()
        states_total_deaths = states_total_deaths[
            states_total_deaths["last_updated"]
            == states_total_deaths["last_updated"].max()
        ].sort_values(
            by=col_deaths, ascending=False
        )  # gets the latest data
        old_index = states_total_deaths["city_name"]
        states_total_deaths = pd.Series(states_total_deaths[col_deaths].values)
        states_total_deaths.index = old_index
        states_total_deaths.index.name = "city_name"
    states_total_deaths = states_total_deaths.sort_values(ascending=False)
    conversion_renames = {}  # saves for renaming later
    for order, item_pair in enumerate(states_total_deaths.iteritems()):
        conversion_renames[item_pair[0]] = item_pair[0] + f" ({order + 1}°)"

    if city_name != None:
        my_city = states_total_deaths.loc[states_total_deaths.index == city_name]

    states_total_deaths = states_total_deaths[:30]

    if city_name != None and city_name not in states_total_deaths.index.values:
        states_total_deaths = states_total_deaths.append(
            my_city
        )  # adds our selected city

    # Ordena por: 1. Dia do máximo, 2. Quantidade de Mortes
    sorted_index = (
        pivot.loc[states_total_deaths.index]
        .idxmax(axis=1)
        .to_frame()
        .merge(states_total_deaths.to_frame(), left_index=True, right_index=True)
    )
    if not deaths_per_cases:
        sorted_index = sorted_index.sort_values(by=[0, col_deaths]).index
    else:
        sorted_index = sorted_index.sort_values(by=["0_x", "0_y"]).index
    states_total_deaths = states_total_deaths.reindex(sorted_index)
    data = _df_to_plotly(pivot.loc[states_total_deaths.index])
    data["y"] = [conversion_renames[city_name] for city_name in data["y"]]
    states_total_deaths.index = [
        conversion_renames[city_name] for city_name in states_total_deaths.index
    ]
    trace1 = go.Heatmap(
        data,
        hoverinfo="text",
        hovertext=_generate_hovertext(data, deaths_per_cases=deaths_per_cases),
        colorscale="temps",
        showscale=False,
    )
    mortes_label = "mortes até hoje"
    if deaths_per_cases:
        mortes_label = "mortes por casos histórico"
    trace2 = go.Bar(
        x=states_total_deaths,
        y=states_total_deaths.index,
        xaxis="x2",
        yaxis="y2",
        orientation="h",
        hoverinfo="text",
        hovertext=[
            "{}: {} {}".format(i[0], i[1], mortes_label)
            for i in zip(states_total_deaths.index, states_total_deaths)
        ],
    )

    d = [trace1, trace2]
    layout = go.Layout(
        title=title,
        plot_bgcolor="rgba(0,0,0,0)",
        # autosize=True,
        # width=1000,
        height=700,
        margin={"l": 100, "r": 100, "t": 30},
        xaxis=dict(domain=[0, 0.8]),
        xaxis2=dict(domain=[0.85, 1]),
        yaxis=dict(tickmode="linear"),
        # yaxis2=dict(tickmode="linear", anchor="x2"),
    )

    fig = go.Figure(data=d, layout=layout)

    st.plotly_chart(fig, use_container_width=True)


def _generate_mvg_deaths(df, place_type, mavg_days, deaths_per_cases=False):
    if deaths_per_cases:
        df = (
            df[~df["deaths"].isnull()][
                [place_type, "last_updated", "deaths", "new_deaths", "confirmed_cases"]
            ]
            .groupby([place_type, "last_updated"])[
                "deaths", "new_deaths", "confirmed_cases"
            ]
            .sum()
            .reset_index()
        )
    else:
        df = (
            df[~df["deaths"].isnull()][
                [place_type, "last_updated", "deaths", "new_deaths"]
            ]
            .groupby([place_type, "last_updated"])["deaths", "new_deaths",]
            .sum()
            .reset_index()
        )

    df["rolling_deaths_new"] = df.groupby(
        place_type, as_index=False, group_keys=False
    ).apply(lambda x: _get_rolling_amount(x, mavg_days))
    if deaths_per_cases:
        df["deaths_per_cases"] = df.apply(make_deaths_per_cases, axis=1)
    return df


def make_deaths_per_cases(row):
    if row["confirmed_cases"] != 0:
        return row["deaths"] / row["confirmed_cases"]
    else:
        return 0


def gen_cards(df, your_city, group):
    # State evalaution
    state_evaluation_df = df.groupby(["last_updated"]).sum().sort_index(ascending=False)
    peak_daily_deaths_day = state_evaluation_df["new_deaths"].idxmax()
    peak_daily_deaths = state_evaluation_df.loc[
        state_evaluation_df.index == peak_daily_deaths_day
    ]["new_deaths"].values[0]

    deaths_behaviour, behaviour_length = evaluate_scrolling_deaths_behaviour(
        state_evaluation_df
    )
    # City evaluation for the banner
    city_evaluation_df = (
        df[df["city_name"] == your_city].groupby(["last_updated"]).sum()
    )
    (
        city_deaths_behaviour,
        city_behaviour_length,
    ) = evaluate_scrolling_deaths_behaviour(city_evaluation_df)
    city_peak_daily_deaths_day = city_evaluation_df["new_deaths"].idxmax()
    city_peak_daily_deaths = city_evaluation_df.loc[
        city_evaluation_df.index == city_peak_daily_deaths_day
    ]["new_deaths"].values[0]
    deaths_banner_design_dict = {
        "stable": {"background-color": "grey", "text": "comportamento estável"},
        "falling": {"background-color": "#0090A7", "text": "queda"},
        "increasing": {"background-color": "#F02C2E", "text": "alta"},
    }

    if city_peak_daily_deaths >= 1:
        pico = f"Seu pico de mortes diárias foi de {city_peak_daily_deaths} mortes em {city_peak_daily_deaths_day.strftime('%d/%m/%Y')}"
    else:
        pico = f"Seu município ainda não reportou nenhuma morte."

    st.write(
        f"""<div class="distancing-cards">
                <div class="distancing-container distancing-card-bg">
                        <div class="distancing-output-wrapper">
                                <span class="distancing-output-row-prediction-label">
                                    Seu estado ({group}) está há 
                                </span>
                                <div class="distancing-output-row">
                                        <span class="distancing-output-row-prediction-value" style="font-size:28px;font-weight:normal;">
                                                <b>{behaviour_length} dia{["","s"][int(behaviour_length> 1)]} em {deaths_banner_design_dict[deaths_behaviour]["text"]}</b>
                                        </span>  
                                </div> 
                                <span class="distancing-output-row-prediction-label">
                                        da média móvel de mortes. O pico de mortes diárias até hoje foi de {peak_daily_deaths} mortes, em {peak_daily_deaths_day.strftime('%d/%m/%Y')}.
                                </span>
                        </div>
                </div>
                <div class="distancing-card-separator"></div>
                <div class="distancing-container distancing-card-bg">
                        <div class="distancing-output-wrapper">
                                <span class="distancing-output-row-prediction-label">
                                        Seu município ({your_city}) está há 
                                </span>
                                <div class="distancing-output-row">
                                        <span class="distancing-output-row-prediction-value" style="font-size:28px;font-weight:normal;">
                                                <b>{city_behaviour_length} dia{["","s"][int(city_behaviour_length> 1)]} em {deaths_banner_design_dict[city_deaths_behaviour]["text"]} </b>
                                        </span>  
                                </div> 
                                <span class="distancing-output-row-prediction-label">
                                        da média móvel de mortes. {pico}
                                </span>
                        </div>
                </div>
            </div>""",
        unsafe_allow_html=True,
    )


# @st.cache(suppress_st_warning=True)
def prepare_heatmap(
    df, place_type, group=None, mavg_days=7, your_city=None, deaths_per_cases=False
):
    refresh = df["data_last_refreshed"].max()
    if place_type == "city_name":
        df = df[df["state_id"] == group]

    if place_type == "city_name" or place_type == "state_id":
        df = _generate_mvg_deaths(
            df, place_type, mavg_days, deaths_per_cases=deaths_per_cases
        )
        col_date = "last_updated"
        col_deaths = "deaths"
        if deaths_per_cases:
            col_deaths = "deaths_per_cases"

    if place_type == "country_pt":
        col_date = "date"
        col_deaths = "total_deaths"

    place_max_deaths = (
        df.groupby(place_type)[[col_deaths]].max().reset_index().sort_values(col_deaths)
    )

    if place_type == "city_name":

        gen_cards(df, your_city, group)
        legend = """
        <div class="base-wrapper">
            O gráfico abaixo mostra a média do número de mortes
            diárias dos últimos cinco dias para os 30 municípios com mais mortes, desde a data da primeira morte reportada e também o que você selecionou mesmo que este não esteja entre os 30 primeiros.
            Para comparação, os números foram normalizados pelo 
            maior valor encontrado em cada município:
            <b>quanto mais vermelho, mais próximo está o valor do
            maior número de mortes por dia observado no município
            até hoje</b>.
            <br><br>
            Os municípios estão ordenadas pelo dia que atingiu o máximo de mortes, 
            ou seja, municípios no pico de mortes aparecerão no topo. {}
            é o município com o maior número de mortos, com: <i>{}</i>
            e o estado totaliza: <i>{}</i>.
            <br><br>
            <i>Última atualização: {}</i>
        </div>
        """

    if place_type == "state_id":

        legend = """
        <div class="base-wrapper">
            <span class="section-header primary-span">ONDA DE MORTES DIÁRIAS POR ESTADO</span>
            <br><br>
            <div class="onda-headercaption">
                O gráfico abaixo mostra a média do número de mortes
                diárias dos últimos cinco dias em cada UF, desde a data da
                primeira morte reportada. Para comparação, os números foram
                normalizados pelo maior valor encontrado em cada UF:
                <b>quanto mais vermelho, mais próximo está o valor do
                maior número de mortes por dia observado na UF até hoje</b>.
                <br><br>
                As UFs estão ordenadas pelo dia que atingiu o máximo de mortes, 
                ou seja, UFs no pico de mortes aparecerão no topo. {}
                é o estado com o maior número de mortos, com: <i>{}</i>
                e o Brasil totaliza: <i>{}</i>.
                <br><br>
                <i>Última atualização: {}</i>
            </div>
        </div>
        """

    if place_type == "country_pt":

        legend = """
        <div class="base-wrapper">
            <span class="section-header primary-span">ONDA DE MORTES DIÁRIAS POR PAÍS</span>
            <br><br>
            O gráfico abaixo mostra a média do número de mortes
            diárias dos últimos cinco dias para os 30 países com mais 
            mortes, desde a data da primeira morte reportada.
            Para comparação, os números foram normalizados pelo maior
            valor encontrado em cada país:<b> quanto mais vermelho,
            mais próximo está o valor do maior número de mortes por
            dia observado no país até hoje</b>.
            <br><br>
            Os países estão ordernados pelo dia que atingiu o máximo de mortes,
            ou seja, os países no pico de mortes aparecerão no topo. {}
            é o país com o maior número de mortos, com: <i>{}</i>
            e o mundo totaliza: <i>{}</i>.
            <br><br>
            <i>Última atualização: {}</i>
        </div>
        """
    if deaths_per_cases:
        legend = """
        <div class="base-wrapper">
            O gráfico abaixo mostra a taxa de mortes
            por casos (acumulado histórico) para os 30 municípios com mais mortes por casos, desde a data da primeira morte reportada e também o que você selecionou mesmo que este não esteja entre os 30 primeiros.
            <b>Quanto mais vermelho, mais próximo está o valor do
            de 1 morte a cada 1 caso registrado no município
            até aquela data.</b>
            <br><br>
            Os municípios estão ordenadas pelo dia que atingiram o seu máximo de mortes por casos, 
            ou seja, municípios no pico de mortes por casos aparecerão no topo. 
            {} é o município com o maior número de mortos por casos, com: <i>{}</i> mortos por casos
            e o estado tem uma mediana de: <i>{}</i> mortos por casos.
            <br><br>
            <i>Última atualização: {}</i>
        </div>
        """
        place_max_deaths = df.reset_index()
        place_max_deaths = place_max_deaths[
            place_max_deaths["last_updated"] == place_max_deaths["last_updated"].max()
        ].sort_values(
            by=col_deaths, ascending=False
        )  # gets the latest data
        old_index = place_max_deaths["city_name"]
        place_max_deaths = pd.Series(place_max_deaths[col_deaths].values)
        place_max_deaths.index = old_index
        place_max_deaths.index.name = "city_name"

        st.write(
            legend.format(
                place_max_deaths.index[0],
                "%0.3f" % place_max_deaths.iloc[0],
                "%0.3f"
                % place_max_deaths.values[int(len(place_max_deaths.values) / 2)],
                refresh[:10],
            ),
            unsafe_allow_html=True,
        )
    else:
        st.write(
            legend.format(
                place_max_deaths.iloc[-1][place_type],
                place_max_deaths.max()[col_deaths],
                place_max_deaths.sum()[col_deaths],
                refresh[:10],
            ),
            unsafe_allow_html=True,
        )

    return plot_heatmap(
        df,
        place_type,
        # min_deaths=min_deaths,
        legend=legend,
        # title ="Distribuição de novas mortes nas UFs (mavg = 5 days)",
        city_name=your_city,
        deaths_per_cases=deaths_per_cases,
    )


def main(session_state=None):
    # Amplitude: Get user info
    user_analytics = amplitude.Amplitude_user()
    user_analytics.gen_user(utils.get_server_session())
    user_analytics.safe_log_event(
        "opened analysis", session_state, is_new_page=True
    )

    utils.localCSS("style.css")
    utils.localCSS("icons.css")

    config = yaml.load(open("configs/config.yaml", "r"), Loader=yaml.FullLoader)
    br_cases = loader.read_data(
        "br", config, endpoint=config["br"]["api"]["endpoints"]["analysis"]["cases"]
    )

    st.write(
        """
        <div class="base-wrapper">
                <span class="section-header primary-span">MORTES DIÁRIAS POR MUNICÍPIO</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_uf = st.selectbox("Selecione um estado para análise:", utils.get_ufs_list())

    prepare_heatmap(
        br_cases, place_type="city_name", group=user_uf,
    )

    prepare_heatmap(
        br_cases, place_type="state_id",
    )

    prepare_heatmap(
        loader.read_data(
            "br", config, endpoint=config["br"]["api"]["endpoints"]["analysis"]["owid"]
        ),
        place_type="country_pt",
    )


def evaluate_scrolling_deaths_behaviour(indf):
    indf = indf.sort_index(ascending=False)
    main_values = indf["rolling_deaths_new"].values
    previous_eval = eval_behaviour(main_values[0], main_values[1])
    for index in range(len(main_values) - 1):
        index = index + 1  # We begin from the second element
        new_eval = eval_behaviour(main_values[index], main_values[index - 1])
        if new_eval != previous_eval:  # If we break the behaviour
            return [previous_eval, index]  # Return the biggest streak possible
    return [previous_eval, len(main_values)]


def eval_behaviour(current_value, previous_value):
    minimal_percentage_for_stable = 0.05
    if (
        previous_value * (1 - minimal_percentage_for_stable)
        <= current_value
        <= previous_value * (1 + minimal_percentage_for_stable)
    ):
        return "stable"
    elif current_value < previous_value:
        return "falling"
    elif current_value > previous_value:
        return "increasing"


if __name__ == "__main__":
    main()
