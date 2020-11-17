import streamlit as st
import utils
import amplitude
from models import Logo


def main(session_state):
    # Amplitude: Get user info
    user_analytics = amplitude.Amplitude_user()
    user_analytics.gen_user(utils.get_server_session())
    user_analytics.safe_log_event(
        "opened who_is", session_state, is_new_page=True
    )
    
    utils.localCSS("style.css")

    st.write(
        """
        <div class="base-wrapper">
            <br><br>
            <a href="https://coronacidades.org/"><img class="coronacidades-logo" src="%s" width="300"/></a><br><br>
                <span>
                Coronacidades é uma plataforma feita para gestores públicos, que reúne
                ferramentas e informações chave para superar a COVID-19.<br>Além dos recursos online, 
                nosso time multidisciplinar está a postos para apoiar municípios e estados
                parceiros no planejamento e implementação de ações específicas nas áreas
                de saúde, assistência social, planejamento e economia. Entre em contato
                conosco.<br><br>
                <i>O CoronaCidades é uma iniciativa da Impulso, do Instituto Arapyau e do
                Instituto de Estudos de Políticas de Saúde (IEPS). 
                <b><a target="_blank" style="color:#3E758A;" href="https://coronacidades.org/pessoas/">Conheça quem faz o Coronacidades.org aqui!</a></b></i>
                </span><br><br><br>
            <a href="https://www.impulsogov.com.br/"><img class="impulso-logo" src="%s" width="150"/></a><br><br>
                <span>
                O FarolCovid e SimulaCovid são desenvolvidos pela Impulso, uma
                organização não-governamental sem fins lucrativos cujo principal
                objetivo é criar capacidade analítica em governos. Fortalecemos o
                processo de coleta e análise de dados para auxiliar gestores públicos na
                tomada de decisão diária, visando aprimoramento contínuo de suas
                políticas.
                </span><br><br>
        </div>
        """
        % (Logo.CORONACIDADES.value, Logo.IMPULSO.value),
        unsafe_allow_html=True,
    )

