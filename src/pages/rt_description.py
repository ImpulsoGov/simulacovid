import streamlit as st
import amplitude
import utils


def main(session_state):
    # Amplitude: Get user info
    user_analytics = amplitude.Amplitude_user()
    user_analytics.gen_user(utils.get_server_session())
    user_analytics.safe_log_event(
        "opened spread_rhythm", session_state, is_new_page=True
    )

    st.header("""Taxa de contágio ($$R_t$$) de Estados e Municípios""")

    st.subheader("""Cálculo da taxa de contágio ($$R_t$$)""")

    st.write(
        """
        O número de reprodução efetivo ($$R_t$$) traduz a quantidade de pessoas que cada pessoa doente infectará em determinado intervalo de tempo. 
        Já o número básico de reprodução ($$R_0$$) da uma doença traduz qual a dinâmica de contágio de todo o curso de transmissão em determinado grupo 
        populacional, sendo, portanto, fixo para a doença. Mas a quantidade de novas infecções geradas por cada pessoa varia ao longo do tempo: se, 
        no início, há menos pessoas imunes, ele tende a ser mais alto; enquanto, tudo mais constante, o aumento da imunidade na população se 
        traduzirá em um número menor de novas infecções. Igualmente, mudanças de comportamento - como a redução de contato entre pessoas ou uso de 
        máscaras, no caso de doenças transmitidas por vias áreas, como a Covid-19 - também influenciam o número de novas infecções.

        A Covid-19 chegou em momentos distintos em cada cidade brasileira e a sociedade também reagiu de maneira diferente em cada uma delas. 
        Portanto, medir o $$R_t$$, traduzindo o $$R_0$$ para o momento específico no qual cada local se encontra, a nível municipal e estadual, traz informações 
        importantes sobre a taxa de contágio da doença. Enquanto o $$R_0$$ é um número geral,
        portanto, o $$R_t$$ então é calculado para cada local e momento no tempo.

        Por exemplo, um $$R_t$$ maior do que 1 indica que, mantendo-se o comportamento e intervenções ativas até aquele dia, ainda há tendência de 
        crescimento exponencial da doença naquela população. Esperamos que cada pessoa infectada naquele momento infectará mais de uma pessoa no futuro - gerando 
        uma curva de contágio que se acelera rapidamente. Portanto, medidas para controlar o contágio têm que ser acirradas. Já um $$R_t$$ abaixo de 
        1 se traduz na expectativa de que o número de novas infecções vai diminuir ao longo do tempo, indicando que a situação está sob controle se todas 
        as medidas e comportamentos forem mantidos.

        Uma boa notícia: por causa da mudança de comportamento, o $$R_t$$ tende a ser menor que o $$R_0$$, como explicam os desenvolvedores do 
        Covid ActNow [1]. Calculá-lo também nos permite, portanto, 
        comparar qual seria a evolução do contágio da Covid-19 caso medidas restritivas de contato e contágio não tivessem sido adotadas.

        Medir diretamente o número efetivo de reprodução da Covid-19 não é possível. Porém, podemos estimar o número de reprodução 
        instantâneo ($$R_t$$) mais provável pelo número de novos casos por dia:

        - Modelo bayesiano no qual o número de novos casos segue uma distribuição de Poisson, e a relação entre os novos casos e $$R_t$$ é dada pela 
        equação encontrada em Bettencourt & Ribeiro [2]:

        """
    )

    st.latex("""k \sim Pois(\lambda), \lambda = k_{t-1} e^{\gamma(R_t-1)}""")

    st.write(
        """
        - A cada nova observação, atualizamos nossa crença em relação ao valor de $$R_t$$ pela regra de Bayes:
        """
    )

    st.latex(
        r"""P(k_t) = \sum_{R_t} P(k_t \mid R_t) P(R_t) \rightarrow P(R_t \mid k_t) = \frac{P(R_t \mid k_t) P(R_t)}{P(k_t)}"""
    )

    st.subheader("""Considerações""")
    st.write(
        r"""
        Reportamos o $$R_t$$ em intervalos de confiança, identificando o valor mais provável.

        - A relação dada por $$\lambda = k_{t-1} e^{\gamma(R_t-1)}$$  é obtida a partir de $$R_0 = \frac{\beta}{\gamma}$$
        tamando $$\beta$$ e $$\gamma$$ fixos, o que não contempla a variabilidade de transmissão devido à intervenções sociais. 
        O *CovidAct Now* [1] sinaliza, por exemplo, o 
        $$R_0$$ como o número pré-intervenção e o $$R_{eff}$$ (efetivo) como pós;

        - O $$R_t$$ deve ser lido como número de novas infecções que são esperadas no tempo serial determinado - estimado em 8 dias para a 
        Covid-19. Ou seja, esperamos que cada pessoa infectada hoje infecte aquele número de novas pessoas nesse intervalo de tempo;
        
        - Seguindo Covid ActNow [3], reportamos o $$R_t$$ de 10 dias 
        atrás - garantindo que não incorreremos em problemas de demora no resultado de testes, por exemplo;

        """
    )

    st.subheader("""Referências""")
    st.write(
        """
        [1] COVID ActNow Blog, 2020. Inference projections for states. Disponível em: 
        https://blog.covidactnow.org/inference-projections-for-states
        
        
        [2] Bettencourt & Ribeiro. 2008. Real Time Bayesian Estimation of the Epidemic Potential of
        Emerging Infectious Diseases. Disponível em: https://doi.org/10.1371/journal.pone.0002185).
        PLoS ONE 3(5): e2185.
        
        
        [3] COVID ActNow Blog, 2020. Modeling metrics critical to reopen safely. Disponível em: 
        https://blog.covidactnow.org/modeling-metrics-critical-to-reopen-safely/
        
        
        [4] Kevin Systrom. 2020. The Metric We Need to Manage COVID-19 (código base). Disponível em:
        http://systrom.com/blog/the-metric-we-need-to-manage-covid-19/
        
        
        [5] Loft-BR. 2020. [Visualizando a evolução do número de reprodução no Brasil (código
        adaptado). Disponível em:
        https://github.com/loft-br/realtime_r0_brazil/blob/master/realtime_r0_bettencourt_ribeiro.ipynb
        
        
        
        [6] COVID ActNow, 2020. [Infer R_t (código adaptado). Disponível em: 
        https://github.com/covid-projections/covid-data-model/blob/089e4e81db32befd6e86e4e105454629fd834ad2/pyseir/inference/infer_rt.py
        """
    )


if __name__ == "__main__":
    main()
