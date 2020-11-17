import streamlit as st
import amplitude
import utils
import yaml
from PIL import Image
from pages import model_description, saude_em_ordem_description, risk_description


def main(session_state):
    # Amplitude: Get user info
    user_analytics = amplitude.Amplitude_user().gen_user(utils.get_server_session())
    user_analytics.safe_log_event(
        event="opened saude_em_ordem_description", session_state=session_state, is_new_page=True
    )

    # Layout
    utils.localCSS("style.css")

    utils.genHeroSection(
        title1="Farol",
        title2="Covid",
        subtitle="Entenda a metodologia da item.",
        logo="https://i.imgur.com/CkYDPR7.png",
        header=True,
    )

    st.write(
        """
        <div class="base-wrapper flex flex-column" style="background-color: rgb(0, 144, 167);">
            <div class="white-span header p1" style="font-size:30px;">MODELOS, LIMITAÇÕES E FONTES</div>
        </div><br><br>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        """<div class="base-wrapper primary-span">
            <span class="section-header">FERRAMENTAS E FONTES</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    item = st.radio(
        "Selecione abaixo um dos itens para ver mais detalhes:",
        [
            "FarolCovid",
            "SimulaCovid",
            "Saúde em Ordem",
            "Fontes de dados e Referências",
        ],
    )

    if item == "FarolCovid":
        st.write(
            """<div class="base-wrapper primary-span">
                <span class="section-header">FAROLCOVID: Como saber se estou no controle da Covid-19?</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        risk_description.main(session_state)

    if item == "SimulaCovid":
        st.write(
            """<div class="base-wrapper primary-span">
                <span class="section-header">SIMULACOVID: Modelo Epidemiológico</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        model_description.main(session_state)

    if item == "Saúde em Ordem":
        st.write(
            """<div class="base-wrapper primary-span">
                <span class="section-header">SAÚDE EM ORDEM</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        saude_em_ordem_description.main(session_state)

    if item == "Fontes de dados e Referências":
        st.write(
            """<div class="base-wrapper primary-span">
                <span class="section-header">FONTES DE DADOS E REFERÊNCIAS</span>
            </div>""",
            unsafe_allow_html=True,
        )

        gen_sources_table()

        st.write(
            """<div class="base-wrapper">
            Agência Nacional de Saúde Suplementar, 2012. Taxa de Ocupação Operacional Geral. Disponível em:
            http://www.ans.gov.br/images/stories/prestadores/E-EFI-03.pdf <br> <br>CDC, 2019. Severe Outcomes
            Among Patients with Coronavirus Disease 2019 (COVID-19) — United States, February 12–March 16, 2020.
            MMWR Morb Mortal Wkly Rep. ePub: 18 March 2020. DOI: http://dx.doi.org/10.15585/mmwr.mm6912e2.<br>
            <br>G. Stein, V. N. Sulzbach and Lazzari. Nota Técnica sobre o Índice Setorial para Distanciamento
            Controlado.  Technical report, 2020<br> <br>Cori, A., Ferguson, N.M., Fraser, C. and Cauchemez, S., 2013. A new framework and software to estimate time-varying reproduction numbers during epidemics. American journal of epidemiology, 178(9), pp.1505-1512. 
            <br> <br> Hill, A, 2020. Model Description. Modelling COVID-19 Spread vs
            Healthcare Capacity. Disponível em: https://alhill.shinyapps.io/COVID19seir/<br> <br>Lazaro Gamio.
            The workers who face the greatest coronavirus risk, 2020.
            https://www.nytimes.com/interactive/2020/03/15/business/economy/coronavirus-worker-risk.html.<br> <br>
            Li, R., Pei, S., Chen, B., Song, Y., Zhang, T., Yang, W., & Shaman, J., 2020. Substantial
            undocumented infection facilitates the rapid dissemination of novel coronavirus (SARS-CoV2).
            Science, 3221(March), eabb3221. DOI: https://doi.org/10.1126/science.abb3221<br> <br>Max Roser, Hannah
            Ritchie, Esteban Ortiz-Ospina and Joe Hasell (2020) - "Coronavirus Disease (COVID-19)". Published
            online at OurWorldInData.org. Retrieved from: 'https://ourworldindata.org/coronavirus' [Online
            Resource]<br> <br>Ministério da Saúde do Brasil, 2020. Boletim Diário. 28 mar. 2020. Disponível em:
            https://www.saude.gov.br/images/pdf/2020/marco/28/28.03%20-%20COVID.pdf
            <br> <br>Nishiura, Hiroshi, Natalie M. Linton, and Andrei R. Akhmetzhanov. "Serial interval of novel coronavirus (COVID-19) infections." International journal of infectious diseases (2020).<br> <br>Vanessa Neumann Sulzbach.
            Essays on Labor Market Polarization in Brazil. Unpublished PhD’s Thesis, 2020.<br> <br>Verity, Robert, et
            al. "Estimates of the severity of coronavirus disease 2019: a model-based analysis." The Lancet
            infectious diseases (2020). Disponível em:
            https://www.medrxiv.org/content/10.1101/2020.03.09.20033357v1 <br> <br>Walker, P.G., Whittaker, C., Watson,
            O., Baguelin, M., Ainslie, K.E.C., Bhatia, S., Bhatt, S., Boonyasiri, A., Boyd, O., Cattarino, L.
            and Cucunubá, Z., 2020. The global impact of COVID-19 and strategies for mitigation and suppression.
            Imperial College London, doi: https://doi. org/10.25561/77735. <br> <br>[1] Wang, C, et al. (2020) Evolving
            Epidemiology and Impact of Non-pharmaceutical Interventions on the Outbreak of Coronavirus Disease
            2019 in Wuhan, China. DOI: https://doi.org/10.1101/2020.03.03.20030593 e pdf de apresentação
            https://docs.google.com/presentation/d/1-rvZs0zsXF_0Tw8TNsBxKH4V1LQQXq7Az9kDfCgZDfE/edit#slide=id.p1
            <br> <br>[2] Wang, J., Zhou, M., & Liu, F., 2020. Reasons for healthcare workers becoming infected with novel
            coronavirus disease 2019 (COVID-19) in China. Journal of Hospital Infection. DOI:
            https://doi.org/10.1016/j.jhin.2020.03.002 <br> <br>Y. O. de Lima, D. M. Costa, and J. M. de Souza. Covid-19:
            Risco de contágio por ocupação no Brasil: Nota metodológica. Technical report, 2020.
            <br>
            </div>""",
            unsafe_allow_html=True,
        )


def gen_sources_table():
    st.write(
        """
        <style type="text/css">
        .tg  {border-collapse:collapse;border-spacing:0;}
        </style>
        <table class="tg" style="undefined;table-layout: fixed; width: 1000px;margin:auto;">
        <colgroup>
        <col style="width: 98px">
        <col style="width: 93px">
        <col style="width: 150px">
        </colgroup>
        <thead>
        <tr>
            <th class="tg-7btt">Dado</th>
            <th class="tg-7btt">Fonte</th>
            <th class="tg-amwm">Data de coleta</th>
        </tr>
        </thead>
        <tbody>
        <tr>
            <td class="tg-fymr">População residente por município e regional de saúde</td>
            <td class="tg-0lax"><a class="github-link" href="https://www.ibge.gov.br/apps/populacao/projecao/">IBGE</a></td>
            <td class="tg-0pky">Dados referentes a 2019. Atualizado diariamente.</td>
        </tr>
        <tr>
            <td class="tg-fymr">Leitos comuns por regional de saúde (clínicos + cirúrgicos  + hospital-dia)</td>
            <td class="tg-0lax"><a class="github-link" href="http://tabnet.datasus.gov.br/cgi/deftohtm.exe?cnes/cnv/leiintbr.def">Cadastro Nacional de Estabelecimentos de Saúde (DATASUS CNES)</a></td>
            <td class="tg-0pky">Dados referentes a junho/2020. Atualizado diariamente.</td>
        </tr>
        <tr>
            <td class="tg-fymr">Leitos UTI por regional de saúde</td>
            <td class="tg-0lax"><a class="github-link" href="http://tabnet.datasus.gov.br/cgi/deftohtm.exe?cnes/cnv/leiutibr.def">Cadastro Nacional de Estabelecimentos de Saúde (DATASUS CNES)</a></td>
            <td class="tg-0pky">Dados referentes a junho/2020. Atualizado diariamente.</td>
        </tr>
        <tr>
            <td class="tg-fymr">Casos e mortes confirmados por município (dados coletados das secretarias de saúde estaduais)</td>
            <td class="tg-0lax"><a class="github-link" href="https://brasil.io/dataset/covid19/boletim">Brasil.io</a></td>
            <td class="tg-0pky">Atualizado diariamente.</td>
        </tr>
        <tr>
            <td class="tg-fymr">Estimativa do número de pessoas com sintomas de síndrome gripal no mercado formal e informal</td>
            <td class="tg-0lax"><a class="github-link" href="https://covid19.ibge.gov.br/pnad-covid/">PNAD Covid</a></td>
            <td class="tg-0pky">Dados referentes a 16/07/2020.</td>
        </tr>
        <tr>
            <td class="tg-fymr">Exposição da ocupação a doenças e infecções e intensidade e extensão de contatos físicos no ambiente de trabalho</td>
            <td class="tg-0lax"><a class="github-link" href="https://www.onetonline.org/">The Occupational Information Network (O*NET)</a></td>
            <td class="tg-0pky">Acesso indireto através do trabalho desenvolvido com o governo do Rio Grande do Sul (RS).</td>
        </tr>
        <tr>
            <td class="tg-fymr">Estimativa do número de empregados de cada ocupação e sua remuneração no setor informal</td>
            <td class="tg-0lax"><a class="github-link" href="">Pesquisa Nacional Domiciliar Contínua (PNADc)</a></td>
            <td class="tg-0pky">Divulgação anual. Última atualização: 2019.</td>
        </tr>
        <tr>
            <td class="tg-fymr">Número de empregados de cada ocupação e sua remuneração no setor formal</td>
            <td class="tg-0lax"><a class="github-link" href="https://www.onetonline.org/">Relação Anual de Informações Sociais (RAIS)</a></td>
            <td class="tg-0pky">Divulgação anual. Última atualização: 2019.</td>
        </tr>
        <tr>
            <td class="tg-fymr">Índice de Isolamento social inLoco dos municípios e estados brasileiros</td>
            <td class="tg-0lax"><a class="github-link" href="https://www.onetonline.org/">inLoco</a></td>
            <td class="tg-0pky">Atualizado diariamente.</td>
        </tr>
        </tr>
        </tbody>
        </table>""",
        unsafe_allow_html=True,
    )
