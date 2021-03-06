import sys

sys.path.append("..")
sys.path.append("../src")

import yaml

config = yaml.load(open("../src/configs/config.yaml", "r"), Loader=yaml.FullLoader)
secrets = yaml.load(open("../src/configs/secrets.yaml", "r"), Loader=yaml.FullLoader)
# TODO: Change this pallete thing to be more standard
# pallete = config[farolcovid][pallete]
pallete = ["#0097A7", "#17A700", "#F2C94C", "#FF5F6B"]
cities_url = (
    "http://datasource.coronacidades.org:7000/" + secrets["inloco"]["cities"]["route"]
)
states_url = (
    "http://datasource.coronacidades.org:7000/" + secrets["inloco"]["states"]["route"]
)
from paths import RAW_PATH, TREAT_PATH, OUTPUT_PATH, FIGURES_PATH, THEMES_PATH

import pandas as pd

pd.options.display.max_columns = 999

import warnings

warnings.filterwarnings("ignore")

# Plotting
import plotly
import plotly.graph_objs as go


def genColor(value):
    critical = 0.50
    bad = 0.70
    if value <= critical:
        return pallete[3]
    elif value <= bad:
        return pallete[2]
    else:
        return pallete[1]


def generateFigsStates(states, clean_df):
    fig = go.Figure()
    buttons_list = [
        dict(
            label="Todos",
            method="update",
            args=[
                {"visible": [True for i in range(len(states))]},
                {
                    "title": "Distanciamento social para os estados selecionados",
                    "annotations": [],
                },
            ],
        )
    ]
    # Add traces
    for a, state_name in enumerate(states):
        xValues = clean_df.columns
        yValues = clean_df.query('state_name == "%s"' % state_name).values[0]
        if len(states) == 1:
            my_line_scheme = dict()
            my_line_scheme["color"] = genColor(yValues[-1])
            fig.add_trace(
                go.Scatter(x=xValues, y=yValues, name=state_name, line=my_line_scheme,)
            )
        else:
            fig.add_trace(go.Scatter(x=xValues, y=yValues, name=state_name,))
        buttons_list.append(
            dict(
                label=state_name,
                method="update",
                args=[
                    {"visible": [i == a for i in range(len(states))]},
                    {
                        "title": "Distanciamento social para %s" % state_name,
                        "annotations": [],
                    },
                ],
            ),
        )

    fig.update_layout(updatemenus=[dict(active=0, buttons=buttons_list,)])
    return fig


def generateFigsCities(city_states_pairs, df):
    fig = go.Figure()
    buttons_list = [
        dict(
            label="Todos",
            method="update",
            args=[
                {"visible": [True for i in range(len(city_states_pairs))]},
                {
                    "title": "Distanciamento social para as cidades selecionados",
                    "annotations": [],
                },
            ],
        )
    ]
    # Add traces
    for a, pair in enumerate(city_states_pairs):
        city_name, state_name = pair
        clean_df = df.query('state_name == "%s"' % state_name).query(
            'city_name == "%s"' % city_name
        )
        if len(city_states_pairs) == 1:
            my_line_scheme = dict()
            my_line_scheme["color"] = genColor(clean_df["isolated"][-1])
            fig.add_trace(
                go.Scatter(
                    x=clean_df["dt"],
                    y=clean_df["isolated"],
                    name=city_name,
                    line=my_line_scheme,
                )
            )
        else:
            fig.add_trace(
                go.Scatter(x=clean_df["dt"], y=clean_df["isolated"], name=city_name,)
            )
        buttons_list.append(
            dict(
                label=city_name,
                method="update",
                args=[
                    {"visible": [i == a for i in range(len(city_states_pairs))]},
                    {
                        "title": "Distanciamento social %s" % city_name,
                        "annotations": [],
                    },
                ],
            ),
        )

    fig.update_layout(updatemenus=[dict(active=0, buttons=buttons_list,)])
    return fig


def gen_social_dist_plots(in_args):
    if type(in_args[0]) == type([]):
        is_city = True
    else:
        is_city = False
    social_dist_plot = None
    if is_city:
        social_dist_df = pd.read_csv(cities_url, index_col=0)
        social_dist_plot = generateFigsCities(in_args, social_dist_df)
    else:  # IS STATE
        social_dist_df = pd.read_csv(states_url, index_col=0)
        my_clean_df = (
            social_dist_df.reset_index()
            .pivot(index="state_name", columns="dt", values="isolated")
            .fillna(0)
            .dropna(how="all")
        )
        social_dist_plot = generateFigsStates(in_args, my_clean_df)
    return social_dist_plot

