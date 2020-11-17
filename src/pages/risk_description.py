import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import amplitude
import utils
import yaml
from pages import rt_description


def main(session_state):
    # Amplitude: Get user info
    user_analytics = amplitude.Amplitude_user()
    user_analytics.gen_user(utils.get_server_session())
    user_analytics.safe_log_event(
        "opened risk_level", session_state, is_new_page=True
    )

    # Config labels
    config = yaml.load(open("configs/config.yaml", "r"), Loader=yaml.FullLoader)
    date_update = config["br"]["farolcovid"]["date_update"]

    # Layout
    utils.localCSS("style.css")

    st.write(
        f"""<div class="base-wrapper"><span class="subsection-header">Atualização - v.2 ({date_update})</span>""",
        unsafe_allow_html=True,
    )

    st.write(
        """<div class="base-wrapper">
            <span class="subsection-header"><b>Níveis de classificação</span></b></br>
            Depois de um primeiro momento de mitigação da Covid-19 nos estados e municípios brasileiros, passamos a uma
            nova fase de resposta à pandemia: a de supressão da doença. Nela, é necessário avaliar
            periodicamente qual o cenário e quais as ações mais adequada para a cidade, regional de
            saúde ou estado, de acordo com indicadores sobre a dinâmica de transmissão da doença e
            sua capacidade de resposta.<br><br> É a partir dessa avaliação que políticas de
            resposta à Covid-19 devem ser calibradas: <b>o objetivo é chegar no "novo normal," onde
            a situação está sob controle.</b> Para auxiliar a população e os gestores públicos nessa
            tarefa, desenvolvemos uma classificação em Níveis de Alerta, baseada em 4 eixos,
            correspondentes a perguntas-chave que devem ser respondidas por quem está tomando
            decisões sobre resposta à pandemia. Adaptamos os antigos "níveis de risco" dos municípios, 
            regiões de saúde e estados com a nova metodologia de <a target="_blank" style="color:#3E758A;" href="https://coronacidades.org/niveis-de-alerta/">Níveis de Alerta</a> 
            desenvolvida pela Vital Strategies e adaptada pela Impulso, composta por 4 níveis:</br>
            <br>
            <li><strong style="color:#F02C2E">Altíssimo</strong>: Há um crescente número de casos de Covid-19 e grande número deles não são detectados</li>
            <li><strong style="color:#F77800">Alto</strong>: Há muitos casos de Covid-19 com transmissão comunitária. A presença de casos não detectados é provável.</li>
            <li><strong style="color:#F7B500">Moderado</strong>: há um número moderado de casos e a maioria tem uma fonte de transmissão conhecida.</li>
            <li><strong style="color:#0090A7">Novo Normal</strong>: casos são raros e técnicas de rastreamento de contato e monitoramento de casos suspeitos evitam disseminação.</li>
            <br></div>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        """<div class="base-wrapper">
        <span class="subsection-header"><b>Classificação</span></b></br>
        A classificação de cada indicador segue a tabela de valores de referência abaixo. Após analisar cada indicador, classificamos 
        o município, regional ou estado no nível de alerta <b>equivalente ao mais alto entre os de cada indicador individual</b>. 
        Caso o município não conte com algum dos indicadores, mostramos o número correspondente para o nível regional. 
        Nesse caso, ele não terá classificação de risco.</div>""",
        unsafe_allow_html=True,
    )

    # Valores de referência
    gen_classification_table(config, date_update)

    st.write(
        """<div class="base-wrapper">
        <span class="subsection-header"><b>Indicadores</span></b></br>
        <br>
        <span class="subsection-header"><b>Situação da Covid-19:</b> Qual a incidência da doença na minha população?</span><br>
        <b>Indicador</b>: Novos casos por 100mil habitantes (média móvel 7 dias).<br>
        <b>Qual sua tendência?</b> Aumentando, estabilizando ou diminuindo?<br><br>
        Utilizamos como indicador nessa dimensão os <b>novos casos reportados de Covid-19 por 100 mil habitantes (medido em média móvel de sete dias)</b>. 
        Essa é uma métrica importante para entender como a doença está atingindo a população no momento atual, e qual sua <b>tendência</b> de evolução dos 
        novos casos - piorando (crescendo pelo menos há 5 dias), melhorando (diminuindo pelo menos há 14 dias) ou estável.</br>
        <br><span class="subsection-header"><b>Controle da Covid-19:</b> Estamos conseguindo frear o surgimento de novos casos?</span><br>
        <b>Indicador</b>: Taxa de contágio (Número efetivo de Reprodução - Rt)<br>
        <b>Qual sua tendência?</b>Aumentado, estabilizando ou diminuindo?<br><br>
        Por não possuirmos dados abertos de testagem estruturados da maioria dos municípios brasileiros, optamos por classificar o controle através da <b>taxa de contágio</b>. 
        Essa métrica busca estimar quantas pessoas em média uma pessoa está infectando hoje - é uma tentativa de entender o espalhamento da doença 
        quando não temos informação de rastreamento de contatos.</br>
        <br>
        Comparado com a versão anterior do Farol, fizemos uma alteração em nosso modelo estatístico de forma <b>a capturar melhor as variações 
        nos novos casos</b>, porém este modelo não se mostrou consistente para algumas cidades. Revertemos o cálculo para o modelo anterior 
        enquanto estudamos uma solução.</br>
        <br><span class="subsection-header"><b>Capacidade do sistema:</b> Como está a capacidade de resposta do sistema de saúde? </span><br>
        <b>Indicador</b>: Dias até atingir ocupação total de leitos UTI<br>
        <b>Qual sua tendência?</b> Aumentado, estabilizando ou diminuindo?<br><br>
        Comparado à versão anterior do Farol Covid, passamos a realizar a projeção de em quanto tempo todos os leitos UTI da regional 
        de saúde (caso município ou região) ou estado estarão ocupados, não mais o número de ventiladores. Realizamos essa mudança por entender 
        que essa rubrica, adotada pelo CNES a partir do mês de maio, traduz de maneira mais fiel a disponibilidade de equipamentos para 
        pacientes Covid. Ajustamos também os valores de referência para ser mais conservadores, observando um período de até 1 mês de cobertura 
        ao invés de 3 meses na versão anterior.</br>
        <br><span class="subsection-header"><b>Confiança nos dados:</b> Quão representativo são os casos oficialmente identificados 
        frente ao total de casos esperados?</span><br>
        <b>Indicador</b>: Taxa de subnotificação<br>
        <b>Qual sua tendência?</b> Aumentado, estabilizando ou diminuindo?<br><br>
        Propomos um 4º nível de análise devido a lidarmos com <b>dados abertos de reporte de casos e 
        mortes</b>, e já ser conhecido o baixo nível de testagem no país. Na versão anterior do Farol já apresentávamos a taxa de subnotificação 
        de casos como uma métrica importante dado o baixo nível de testagem e protocolos de reporte de casos com sintomas avançados para mostrar 
        o quanto possivelmente não estamos observando do espalhamento da doença.</br>
        <br>
        Na nova versão, junto à organização ModCovid com pesquisadores da USP, ajustamos a taxa de notificação para capturar melhor 
        características locais, com base na distribuição etária do município, região ou estado e na incidência da doença em diferentes 
        faixas etárias, e também estimar casos assintomáticos. <b>Isso fez com que alguns municípios que tinham uma baixa subnotificação 
        aumentassem seu nível de alerta</b>, pois consideramos os casos assintomáticos agora nessa métrica. Em contrapartida, ajustamos os 
        valores de referência dos níveis de subnotificação considerando cerca de 30%, de casos assintomáticos, que são de extrema dificuldade 
        de serem diagnosticados.
        </div>""",
        unsafe_allow_html=True,
    )

    # Limitação
    st.write(
        """<div class="base-wrapper"><span class="subsection-header"><b>Essas métricas são suficientes?</b></span><br>
        <b>Não.</b><br><br>Desenvolvemos os níveis de alerta do FarolCovid com dados públicos e abertos, disponíveis
        online. É um primeiro passo para o gestor orientar sua tomada de decisão de maneira informada,
        orientado por dados que o atualizam tanto sobre o estágio de evolução da doença em seu local 
        quanto sua capacidade de resposta. O gestor público, entretanto, conta com uma riqueza
        maior de informações que deve ser utilizada na formulação de respostas adequadas à sua realidade.
        Informações como a quantidade de testes realizados, a taxa de pessoas que testam positivo e o tempo
        médio de internação são outros fatores importantes para a tomada de decisão. Estamos à disposição
        para apoiar o gestor público a aprofundar a análise para seu estado ou município, de forma
        inteiramente gratuita. <a class="github-link" href="https://coronacidades.org/fale-conosco/>Entre em contato pelo Coronacidades.org</a>!
        </div>""",
        unsafe_allow_html=True,
    )

    # Detalhes dos indicadores
    gen_indicators_details(session_state, date_update)


def gen_distribution_details():

    st.write(
        """<div class="base-wrapper"><span class="subsection-header"><b>Detalhes da distribuição dos indicadores-chave</b></span><br>
        Para ilustrar as classificações dos indicadores, geramos os gráficos das distribuições de cada indicador 
        (diagonal) e as distribuições por pares de indicadores (em cada eixo) abaixo, para cidades, regionais e estados.
        </div>""",
        unsafe_allow_html=True,
    )

    st.image(
        Image.open("imgs/methodology_v2/cities_indicators_20200915.png"),
        use_column_width=True,
        caption="Distribuição de indicadores-chaves para cidades (retrato de 15/set/2020. Cada ponto representa uma cidade, os eixos x e y trazem os valores dos indicadores-chaves para aquela cidade. Na diagonal segue o histograma do indicador-chave.",
    )

    st.image(
        Image.open("imgs/methodology_v2/health_region_indicators_20200915.png"),
        use_column_width=True,
        caption="Distribuição de indicadores-chaves para regionais de saúde (retrato de 15/set/2020). Cada ponto representa uma estado, os eixos x e y trazem os valores dos indicadores-chaves para aquela cidade. Na diagonal segue o histograma do indicador-chave.",
    )

    st.image(
        Image.open("imgs/methodology_v2/states_indicators_20200915.png"),
        use_column_width=True,
        caption="Distribuição de indicadores-chaves para estados (retrato de 15/set/2020). Cada ponto representa uma estado, os eixos x e y trazem os valores dos indicadores-chaves para aquela cidade. Na diagonal segue o histograma do indicador-chave.",
    )


def gen_indicators_details(session_state, date_update):
    st.write(
        """<div class="base-wrapper primary-span">
            <span class="section-header">CÁLCULO E CLASSIFICAÇÃO DE INDICADORES</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    indicador = st.radio(
        "Selecione abaixo o indicador para ver a descrição em detalhe:",
        [
            f"GERAL: Distribuição dos indicadores chaves em {date_update}",
            "SITUAÇÃO DA DOENÇA: Média móvel de novos casos por 100 mil habitantes",
            "CONTROLE DA DOENÇA: Taxa de contágio (Rt)",
            "CAPACIDADE DO SISTEMA: Dias até atingir ocupação total de leitos UTI-Covid",
            "CONFIANÇA NOS DADOS: Taxa de subnotificação de casos",
        ],
    )

    if indicador == f"GERAL: Distribuição dos indicadores chaves em {date_update}":
        gen_distribution_details()

    if (
        indicador
        == "SITUAÇÃO DA DOENÇA: Média móvel de novos casos por 100 mil habitantes"
    ):
        st.write(
            """<div class="base-wrapper primary-span">
                <span class="section-header">SITUAÇÃO DA DOENÇA: Média móvel de novos casos por 100 mil habitantes</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write(
            """<div class="base-wrapper">
            <span class="subsection-header"><b>Como saber o quão crítico é o nível de novos casos?</b></span><br> 
            Para responder essa pergunta precisamos entender como vem evoluindo a incidência dos casos na
            população ao longo do tempo e onde estamos nessa curva. Logo, os valores de referência para a
            classificação dos níveis de alerta foram definidos com base na série histórica de novos casos de
            Covid-19 nas capitais brasileiras, por maior consistência no reporte de casos e também maior período
            de tempo transcorrido desde o 1º caso. 
            Como calculamos os valores de referência?  Dada a série histórica, com a média móvel semanal de
            novos casos diários por 100mil habitantes das capitais, separamos a distribuição de novos casos por
            dia das capitais em 4 intervalos traduzidos nos quartis:<br>
            <li>Novo normal (Q1): máximo dentre 25% dos menores valores de novos casos diários;</li>
            <li>Moderado (Q2):máximo dentre 50% dos menores valores de novos casos diários;</li>
            <li>Alto (Q3): máximo dentre 75% dosmenores valores de novos casos diários; </li>
            <li>Altíssimo: todos os valores acima do classificado para alto.</li><br>
            O valor final é dado pela média dos quartis das capitais. Tomemos o exemplo de Aracaju: abaixo temos
            a distribuição da média de novos casos até 30/08/2020. Até esta data, 25% dos dias tiveram uma média
            de até 1.7 por 100 mil habitantes (novo normal); 50% dos dias tiveram uma média até de 22.7
            (moderado); e 75% foram abaixo de 61.3 (alto - os valores acima deste são considerados altíssimo).
            </div>""",
            unsafe_allow_html=True,
        )

        st.image(
            Image.open("imgs/methodology_v2/new_cases_aracaju_20200830.png"),
            use_column_width=True,
            caption="Distribuição da média móvel semanal de novos casos por 100mil habitantes em Aracaju (retrato de 30/ago/2020).",
        )

        st.write(
            """<div class="base-wrapper">
            A distribuição de todas as capitais abaixo reflete parte da variação local de
            intensidade e progressão da doença em diferentes localidades do Brasil. A média dos
            quartis de todas as capitais nos fornece os valores de referência utilizados para a
            classificação da Situação da doença - novo normal até 3.7 (Q1); moderado até 12.5 (Q2);
            alto até 27.4 (Q3); altíssimo acima de 27.4.
            </div>""",
            unsafe_allow_html=True,
        )

        st.image(
            Image.open("imgs/methodology_v2/new_cases_capitals_20200830.png"),
            use_column_width=True,
            caption="Distribuição da média móvel semanal de novos casos por 100mil habitantes para todas as capitais (retrato de 30/ago/2020).",
        )

        st.write(
            """<div class="base-wrapper">
            <span class="subsection-header"><b>LIMITAÇÕES</b></span><br> 
            <li>Utilizamos dados abertos de casos reportados - ou seja, as datas são do reporte do caso e não do
            início dos sintomas. Como sabemos que existe um  atraso entre o início dos sintomas e a inserção do
            resultado do teste no sistema, os valores não traduzem fielmente a realidade do dia de hoje.</li>
            <li>Existe viés de seleção atrelado ao período de evolução da doença que não observamos ainda. Isso ocorre
            pois nenhuma das capitais extinguiram o número de novos casos diários até a 30/08/2020. Caso a
            tendência seja somente de diminuição do número de casos a partir de hoje, por exemplo, os valores de
            referência estariam superestimados.</li>
            <li> Existe também viés de seleção relacionado ao porte das capitais. 
            Por um lado, estas possuem maior densidade populacional, o que aumenta a chance de terem
            maior número de casos, mas por outro lado, também possuem maior infraestrutura para resposta à
            crise. Estas foram escolhidas por ter uma maior estabilidade no reporte dos casos e maior número de
            testes RT-PCR dentre os testes realizados (que indica a presença ativa do vírus no organismo).</li>
            </div>""",
            unsafe_allow_html=True,
        )

    if indicador == "CONFIANÇA NOS DADOS: Taxa de subnotificação de casos":

        st.write(
            """<div class="base-wrapper primary-span">
                <span class="section-header">CONFIANÇA NOS DADOS: Taxa de subnotificação de casos</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write(
            """<div class="base-wrapper">
                <span class="subsection-header"><b>O que é?</b></span><br> 
                Um modelo de subnotificação é uma ferramenta estatística utilizada para auxiliar a compreensão da
                real situação de infectados num determinado local, pois os dados de casos reportados não refletem
                perfeitamente a realidade, uma vez que há - por diversas razões - casos não identificados
                oficialmente. Alguns dos fatores que aumentam o grau de subnotificação são a falta de testagem
                massiva na população; detecção de casos somente após apresentação de sintomas; e a própria
                característica da doença de existirem infectados assintomáticos, que são transmissores ainda que em
                menor escala (WHO, 2020).
                <br><br><span class="subsection-header"><b>Como foi desenvolvido?</b></span><br> 
                O modelo de subnotificação do grupo de pesquisa <a class="github-link" href='http://www.cemeai.icmc.usp.br/ModCovid19/'>ModCovid</a> 
                foi desenvolvido inicialmente para ajudar a determinar o estágio da epidemia em Aracaju e Maceió.
                <br><br><span class="subsection-header"><b>Por que é importante?</b></span><br> 
                Para a evolução da epidemia numa região precisamos descobrir quantos novos casos de infecção são
                gerados a cada dia, a partir de um certo momento no tempo. Porém, sabemos que a medição desses casos
                é deficiente, principalmente por gargalos na testagem de Covid-19 em nosso país. Portanto,
                calculamos um número corrigido de casos a partir de comparações com proporções esperadas de mortes
                para casos, conforme a literatura nascente sobre a dinâmica da Covid-19 em diferentes populações.
                Isso nos permite planejar novas ações de combate à disseminação, sua ordem de prioridade e
                preparação para novos leitos de atendimento.
                <br><br><span class="subsection-header"><b>Como o modelo funciona?</b></span><br> 
                Fazemos uma regressão a partir do número de mortos reportados por Covid-19 para estimar o número
                de casos de pessoas infectadas 14 dias compatível com aquela quantidade de mortes. Ao compará-lo com
                a quantidade de casos registrados, calculamos a taxa de subnotificação correspondente. O período de
                14 dias é um tempo médio aproximado para a evolução da doença do momento da infecção até o
                falecimento de um indivíduo (Alison, 2020).
                <br><br><span class="subsection-header"><b>Como é feito o cálculo</b></span><br> 
                Utilizando uma <a class="github-link" href="https://www.inf.ufsc.br/~andre.zibetti/probabilidade/binomial_negativa.html">distribuição binomial negativa</a> 
                como modelo probabilístico, o cálculo gera o número de casos positivos que seriam esperados dado o número mortes observadas.
                A distribuição modela a probabilidade de que um número  de novos infectados possa falecer 14 dias
                após de ter se tornado infeccioso, dado o total de mortes até a data (D) e a taxa de mortalidade por
                infecção (IFR). A taxa de mortalidade por infecção (IFR) das regiões é calculada utilizando IFRs por
                faixa etária estimados em Hubei, segundo Verity, Robert, et al. (2020)[1], e obtém-se a IFR total da
                região ponderada pela população em cada faixa com os dados da População Residente (CNES - 2019).<br><br>
                Selecionamos a série histórica de mortes da região a partir da 15a morte e com pelo menos 15 dias
                desde o 1o caso, de maneira a garantir significância estatística. Dado o total de mortes  e a IFR,
                realizamos 100.000 simulações para cada data da série e os casos estimados são dados pelo valor
                médio da distribuição gerada.
                <br><br><span class="subsection-header"><b>LIMITES E CONSIDERAÇÕES SOBRE O MODELO</b></span><br> 
                <li>Existe atraso na confirmação do diagnóstico de mortes por Covid-19, logo a data do reporte não
                reflete a data real de quando ocorreu o óbito. Isso significa que estamos olhando muitas vezes para
                um retrato do passado e não de agora. Quanto maior o atraso no reporte, menos ajustada está a taxa
                de subnotificação à realidade atual.</li>
                <li>Existe subnotificação de mortes que ocorrem fora do ambiente
                hospitalar, que podem influenciar sensivelmente as estimativas. Quem morre de Covid-19 em casa não é
                necessariamente reportado nas estatísticas de óbito por Covid e portanto leva a subestimarmos o
                tamanho da subnotificação.</li>
                <li>Existem inconsistências no reporte de mortes por Covid-19. Há uma
                superestimação da subnotificação atrelada à protocolos de notificação independente da causa
                principal da morte ser Covid-19.</li>
                <br>Outras opções para a estimação de infecciosos podem ser o uso de
                pacientes com Síndrome Respiratória Aguda Grave (SRAG), pacientes em leitos hospitalares de
                retaguarda e pacientes internados em leitos de UTI. Essas estratégias, porém, podem ser ainda mais
                imprecisas, uma vez que há uma grande incerteza envolvendo questões básicas como o número total de
                leitos disponíveis (SUS e particulares), etiologia dos casos de SRAG e disponibilidade local de
                UTIs. Neste momento, com uma amostragem relativamente pequena no início da epidemia, a estimação
                dos infecciosos usando a série histórica dos mortos se mostra a melhor opção. Reiteramos que dados
                de testagem massiva e estruturada em modelos estatísticos e probabilísticos são essenciais para o
                controle da evolução da doença em um futuro próximo.
                </div>""",
            unsafe_allow_html=True,
        )

    if indicador == "CONTROLE DA DOENÇA: Taxa de contágio (Rt)":

        st.write(
            """<div class="base-wrapper primary-span">
                <span class="section-header">CONTROLE DA DOENÇA: Taxa de contágio (Rt)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        rt_description.main(session_state)

        # st.write(
        #     """<div class="base-wrapper">
        #     <span class="subsection-header"><b>O que é?</b></span><br>
        #     O número de reprodução efetivo (Rt) traduz a quantidade de pessoas que cada pessoa
        #     doente infectará em determinado intervalo de tempo.  Já o número básico de reprodução
        #     (<i>R0</i>) da uma doença traduz qual a dinâmica de contágio de todo o curso de transmissão em
        #     determinado grupo populacional, sendo, portanto, fixo para a doença. Mas a quantidade de
        #     novas infecções geradas por cada pessoa varia ao longo do tempo: se, no início, há menos
        #     pessoas imunes, ele tende a ser mais alto; enquanto, tudo mais constante, o aumento da
        #     imunidade na população se traduzirá em um número menor de novas infecções. Igualmente,
        #     mudanças de comportamento - como a redução de contato entre pessoas ou uso de máscaras, no
        #     caso de doenças transmitidas por vias áreas, como a Covid-19 - também influenciam o número
        #     de novas infecções.<br><br> A Covid-19 chegou em momentos distintos em cada cidade brasileira e
        #     a sociedade também reagiu de maneira diferente em cada uma delas. Portanto, medir o
        #     <i>Rt</i>, traduzindo o <i>R0</i> para o momento específico no qual cada local se encontra, a
        #     nível municipal e estadual, traz informações importantes sobre a taxa de contágio da doença.
        #     Enquanto o <i>R0</i> é um número geral, portanto, o  então é calculado para cada local e
        #     momento no tempo. Por exemplo, um <i>Rt</i> maior do que 1 indica que, mantendo-se o
        #     comportamento e intervenções ativas até aquele dia, ainda há tendência de crescimento
        #     exponencial da doença naquela população. Esperamos que cada pessoa infectada naquele momento
        #     infectará mais de uma pessoa no futuro - gerando uma curva de contágio que se acelera
        #     rapidamente. Já um <i>Rt</i> abaixo de 1 se traduz na expectativa de que o número de novas infecções
        #     vai diminuir ao longo do tempo, indicando que a situação está sob controle se todas as medidas e
        #     comportamentos forem mantidos.<br><br>Uma boa notícia: por causa da mudança de comportamento, o
        #     <i>Rt</i> tende a ser menor que o <i>R0</i>, como explicam os desenvolvedores do
        #     <i>CovidActNow</i>. Calculá-lo também nos permite, portanto, comparar qual seria a evolução
        #     do contágio da Covid-19 caso medidas restritivas de contato e contágio não tivessem sido
        #     adotadas.<br> Medir diretamente o número efetivo de reprodução da Covid-19 não é possível.
        #     Porém, podemos estimar o número de reprodução instantâneo (<i>Rt</i>) mais provável pelo
        #     número de novos casos por dia.<br><br>
        #     <span class="subsection-header"><b>Como funciona o modelo?</b></span><br>
        #     O modelo utilizado para o cálculo do Rt foi desenvolvido por Cori et.
        #     al (2013) e implementado no pacote <i>EpiEstim</i>, podendo ser utilizado no R (linguagem de
        #     programação) ou no Excel. Ele toma como entrada a série de casos da doença na população e
        #     estima o Rt utilizando um modelo bayesiano. Esse modelo estima a distribuição a posteriori
        #     do Rt dado o número de casos ativos no tempo <i>t</i> e a infectividadde da doença no local.
        #     A infectividade pode ser entendida como a probabilidade de um indivíduo infectar pessoas o
        #     momento de evolução da doenca no qual se encontra - por exemplo, um indivíduo com Covid no
        #     4º dia de sintomas é mais infeccioso que o um indivíduo no 15º dia.  Esse valor não é
        #     observado, portanto, é estimado pela distribuição esperada do tempo de geração da doença
        #     (intevalo serial) - que é o tempo esperado entre uma pessoa apresentar os sintomas e uma
        #     pessoa contaminada por esta passar a apresentar os sintomas da doença. Esse número para a
        #     Covid hoje segue uma distribuição com média de 4.7 e desvio padrão de 2.9 (Hiroshi, 2020).<br><br>
        #     Dada a série de novos casos por dia, e a média e desvio padrão do intervalo serial, o modelo
        #     então estima o valor mais provável do número de reprodução básica da doença no tempo
        #     <i>t</i> e os respectivos intervalos de confiança. Utilizamos o intevalo de 95% de confiança
        #     para reportar as estimativas.
        #     </div>""",
        #     unsafe_allow_html=True,
        # )

    if (
        indicador
        == "CAPACIDADE DO SISTEMA: Dias até atingir ocupação total de leitos UTI-Covid"
    ):

        st.write(
            """<div class="base-wrapper">Ver metodologia do SimulaCovid: a capacidade hospitalar é projetada com os dados mais recentes da doença no município, regional ou estado.
                </div>""",
            unsafe_allow_html=True,
        )


def gen_classification_table(config, date_update):

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

    st.write(
        """<div class="base-wrapper"><div style="margin: 10px 10px 10px 10px;">
            <div style="font-size: 14px">
                Atualizado em: %s
            </div>
            <div class="info-div-table" style="height: auto;">
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
                    <td class="light-blue-bg bold"><span>x&lt;=%s</span></td>
                    <td class="light-yellow-bg bold"><span>%s&lt;x&lt;=%s</span></td>
                    <td class="light-orange-bg bold"><span>%s&lt;=x&lt;=%s</span></td>
                    <td class="light-red-bg bold"><span>x &gt;= %s</span></td>
                </tr>
                <tr>
                    <td><span>Tendência de novos casos diários</span></td>
                    <td class="lightgrey-bg" colspan="4"><span>Se crescendo*, mover para o nível mais alto</span></td>
                </tr>
                <tr>
                    <td><span>Controle da doença</span></td>
                    <td><span>Número de reprodução efetiva</span></td>
                    <td class="light-blue-bg bold"><span>&lt;%s</span></td>
                    <td class="light-yellow-bg bold"><span>&lt;%s - %s&gt;</span></td>
                    <td class="light-orange-bg bold"><span>&lt;%s - %s&gt;</span>&nbsp;</td>
                    <td class="light-red-bg bold"><span>&gt;%s</span></td>
                </tr>
                <tr>
                    <td><span>Capacidade de respostas do sistema de saúde</span></td>
                    <td><span>Projeção de tempo para ocupação total de leitos UTI</span></td>
                    <td class="light-blue-bg bold">%s - 90 dias</td>
                    <td class="light-yellow-bg bold"><span>%s - %s dias</span></td>
                    <td class="light-orange-bg bold"><span>%s - %s dias</span></td>
                    <td class="light-red-bg bold"><span>%s - %s dias</span></td>
                </tr>
                <tr>
                    <td><span>Confiança dos dados</span></td>
                    <td><span>Subnotificação (casos <b>não</b> diagnosticados a cada 10 infectados)</span></td>
                    <td class="light-blue-bg bold"><span>%s&lt;=x&lt;%a</span></td>
                    <td class="light-yellow-bg bold"><span>%s&lt;=x&lt;%s</span></td>
                    <td class="light-orange-bg bold"><span>%s&lt;=x&lt;%s</span></td>
                    <td class="light-red-bg bold"><span>%s&lt;=x&lt;=10</span></td>
                </tr>
            </tbody>
            </table>
            </div>
            <div style="font-size: 14px">
                * Como determinamos a tendência:
                <ul class="sub"> 
                    <li> Crescendo: caso o aumento de novos casos esteja acontecendo por pelo menos 5 dias. </li>
                    <li> Descrescendo: caso a diminuição de novos casos esteja acontecendo por pelo menos 14 dias. </li>
                    <li> Estabilizando: qualquer outra mudança. </li>
                </ul>
            </div>
            </div>
        </div>"""
        % (
            date_update,
            situation_classification[1],
            situation_classification[1],
            situation_classification[2],
            situation_classification[2],
            situation_classification[3],
            situation_classification[3],
            control_classification[1],
            control_classification[1],
            control_classification[2],
            control_classification[2],
            control_classification[3],
            control_classification[3],
            capacity_classification[3],
            capacity_classification[2],
            capacity_classification[3],
            capacity_classification[1],
            capacity_classification[2],
            capacity_classification[0],
            capacity_classification[1],
            int(trust_classification[0] * 10),
            int(trust_classification[1] * 10),
            int(trust_classification[1] * 10),
            int(trust_classification[2] * 10),
            int(trust_classification[2] * 10),
            int(trust_classification[3] * 10),
            int(trust_classification[3] * 10),
        ),
        unsafe_allow_html=True,
    )


# def main(session_state):
#     user_analytics = amplitude.gen_user(utils.get_server_session())
#     opening_response = user_analytics.safe_log_event(
#         "opened risk_level", session_state, is_new_page=True
#     )
#     st.header("""Níveis de Risco: como saber se estou no controle da Covid-19?""")

#     st.write(
#         """
#         <br>
#         Até que uma vacina ou tratamento sejam encontrados para a Covid-19, será
#         necessário <strong>controlar a quantidade de pessoas infectadas, para
#         ter certeza de que o sistema de saúde terá capacidade de atender a todas
#         e todos, e não venha a colapsar.</strong><br><br> Depois de um primeiro
#         momento de mitigação da Covid-19 nos estados e municípios brasileiros,
#         passamos a uma nova fase da resposta à pandemia, quando será necessário
#         avaliar, a cada momento, qual a abordagem mais adequada para seu
#         município ou estado, de acordo com informações sobre a dinâmica de
#         transmissão da doença e sua capacidade de resposta.<br><br> Enquanto
#         muitas cidades já convivem com um número alto de casos diagnosticados,
#         outros municípios ainda não registram internações ou óbitos por
#         Covid-19. Tampouco o "pico" do número de casos e óbitos será atingido ao
#         mesmo tempo em todo o território.<br><br> Ainda que haja medidas
#         indicadas para todas as situações, como os protocolos de higienização e
#         a adoção de um espaço de segurança entre as pessoas em espaços
#         compartilhados, em um país de dimensões continentais como o Brasil, a
#         resposta à pandemia do coronavírus precisa considerar a capacidade
#         hospitalar de cada região e o momento onde cada um se encontra na
#         evolução da doença.<br><br>
#     """,
#         unsafe_allow_html=True,
#     )

#     st.subheader("Indicadores-chave")

#     st.write(
#         """
#         Para desenvolver
#         os níveis de risco do FarolCovid, avaliamos três
#         indicadores-chave:<br><br>
#         <li><strong>Ritmo de contágio (Rt),</strong> que
#         traduz para quantas pessoas cada pessoa doente transmitirá a doença. Ele
#         é calculado por meio de uma atualização do estimador do número efetivo
#         de reprodução da Covid-19, a partir do número de novos casos registrados
#         por dia. O Ritmo de contágio indica qual é o cenário futuro esperado
#         para a doença. Para mais informações de como esse número é calculado,
#         acesse nossa metodologia do estimador de Rt na aba à
#         esquerda.
#         </li><li><strong>Taxa de subnotificação,</strong> que estima a
#         quantidade de pessoas doentes que não são diagnosticadas. Ela é
#         calculada considerando uma taxa de mortalidade padrão de 2% e estimando
#         quantos casos teriam que estar ativos para produzir o número de mortos
#         registrados naquele estado ou município. É um indicador da necessidade
#         de realizar mais testes na população. Para mais informações sobre como
#         esse número é calculado, acesse nossa metodologia na aba à
#         esquerda.
#         </li><li><strong>Capacidade hospitalar,</strong> que reporta a
#         estimativa do número de dias até que todos os leitos da rede de saúde
#         disponíveis para Covid-19 estarão ocupados. Ela é feita utilizando o
#         modelo do SimulaCovid calibrado com o ritmo de contágio atual. É um
#         indicador do tempo que o gestor pode ter para reagir, caso venha a
#         registrar um aumento inesperado no número de casos. Para mais
#         informações sobre como esse número é calculado, acesse nossa metodologia
#         do modelo na aba à esquerda.<br><br>
#         </li>Ainda não há estudos científicos
#         que indiquem a relação exata entre a Taxa de Isolamento e o seu impacto
#         no Ritmo de Contágio para municípios brasileiros; portanto, essa versão
#         do FarolCovid informa ao gestor público qual é o nível de isolamento
#         social, mas não o inclui no cálculo para classificação de níveis de
#         risco.<br><br>
#         """,
#         unsafe_allow_html=True,
#     )

#     st.write(
#         """
#         Avaliamos se os três indicadores-chave estão bons, insatisfatórios ou
#         ruins, avaliamos suas tendências (se estão crescendo, estáveis ou
#         diminuindo) e então classificamos o município ou estado no nível de
#         risco equivalente: baixo, médio ou alto risco de colapso do sistema de
#         saúde.<br><br> Os indicadores são avaliados da seguinte forma:<br><br>
#         <ul>
#             <li><strong>Ritmo de Contágio</strong><br><br>
#             <ul>
#                 <li><strong style="color:green">Bom</strong>: < 1, indicando que cada pessoa doente infecta menos de uma nova pessoa;</li>
#                 <li><strong style="color:	orange">Insatisfatório</strong>: entre 1 e 1.2, indicando o início de um comportamento exponencial de crescimento do número de pessoas doentes;</li>
#                 <li><strong style="color:red">Ruim</strong>: > 1.2, indicando que há um crescimento exponencial do número de pessoas sendo infectadas.</li>
#             </ul>
#                     </li>
#             <li><strong>Tendência do ritmo de contágio</strong><br><br>
#             <ul>
#                 <li><strong style="color:green">Descendo</strong>: A taxa reportada há 10 dias é menor do que aquela reportada 17 dias atrás, indicando que o ritmo de contágio pode ter continuado a cair nos últimos 10 dias;</li>
#                 <li><strong style="color:orange">Estável</strong>: A taxa reportada há 10 dias é 0.9 a 1.1 vezes aquela reportada 17 dias atrás, indicando que o ritmo de contágio pode ter se mantido semelhante nos últimos 10 dias;</li>
#                 <li><strong style="color:red">Subindo</strong>: A taxa reportada há 10 dias é maior do que aquela reportada 17 dias atrás, indicando que o ritmo de contágio tenha continuado a subir nos últimos 10 dias.</li>
#             </ul> </li>
#             <li><strong>Taxa de subnotificação</strong><br><br>
#             <ul>
#                     <li><strong style="color:green">Bom</strong>: < 50%, indicando que o número de casos registrados não está tão distante do esperado quando comparado com o número de mortos. Aceitamos esse limite de 50% pois pode ser o caso da mortalidade ser mais alta naquele município ou estado por um padrão de vulnerabilidade da população;</li>
#                 <li><strong style="color:orange">Insatisfatório</strong>: entre 50 e 70%, indicando que o número de casos registrados está distante do esperado quando comparado com o número de mortos;</li>
#                 <li><strong style="color:red">Ruim</strong>: > 70%. Indica que o número de casos registrados está muito pequeno quando comparado com o número de mortos confirmados com Covid-19. Indica que há falta de testagem.</li>
#             </ul> </li>
#             <li><strong>Capacidade Hospitalar</strong><br><br>
#             <ul>
#                 <li><strong style="color:green">Bom</strong>: > 60 dias até que todos os leitos estejam ocupados com pacientes com Covid-19, indicando que o poder público terá tempo para organizar uma resposta caso o número de casos venha a crescer de modo inesperado;</li>
#                 <li><strong style="color:orange">Insatisfatório</strong>: entre 30 e 60 dias até que todos os leitos estejam ocupados com pacientes com Covid-19;</li>
#                 <li><strong style="color:red">Ruim</strong>: < 30 até que todos os leitos estejam ocupados com pacientes com Covid-19, indicando que o gestor terá pouco tempo de reação antes do colapso do sistema de saúde, caso haja um crescimento inesperado no número de casos.</li>
#             </ul> </li>
#         </ul>
#         <br>
#     """,
#         unsafe_allow_html=True,
#     )

#     st.subheader("Regras de classificação para os níveis de risco")
#     st.write(
#         """
#         Inspirados pelo modelo do Rio Grande
#         do Sul [1], desenvolvemos um sistema de níveis de risco de colapso do
#         sistema de saúde, seja por um ritmo de contágio mais elevado ou por uma
#         baixa capacidade do sistema em si.<br><br> A classificação em níveis de
#         risco é <strong>dinâmica</strong>, indicando que ela muda conforme os
#         indicadores das cidades e municípios são atualizados, diariamente.
#         Portanto, aconselhamos que seja feito um acompanhamento frequente do
#         FarolCovid por parte de gestores.<br><br> Esses números podem, ainda,
#         ser uma importante ferramenta para comunicação com os cidadãos, servindo
#         de embasamento e justificativa para a tomada de decisão adequada a cada
#         realidade local. O público, em geral, também pode utilizar esses números
#         para engajar o poder público em um debate informado sobre quais são as
#         melhores políticas para sua cidade ou Estado.<br><br>
#     """,
#         unsafe_allow_html=True,
#     )

#     st.image(
#         Image.open("imgs/semaforo0.png"),
#         use_column_width=True,
#         caption="Imagem meramente ilustrativa",
#     )

#     st.write(
#         """
#         <span>
#         Dizemos que município está no <strong style="color:green">Nível de Risco BAIXO</strong>  se satisfizer todos os seguintes requisitos:<br><br>
#             <ul>
#                 <li><strong>Ritmo de contágio </strong> <strong style="color:green">Bom</strong> (Rt < 1.0),
#                     indicando que o número de pessoas doentes está decrescendo;</li>
#                 <li><strong>Ritmo de contágio em tendência </strong><strong style="color:orange"> estável</strong> <strong> ou</strong>
#                      </strong><strong style="color:green">queda</strong>, indicando que esperamos que o ritmo de contágio não retomará
#                      uma trajetória ascendente;</li>
#                 <li><strong>Subnotificação </strong><strong style="color:green">Bom</strong> (< 50%),
#                     indicando haver um bom nível de testagem da população;</li>
#                 <li><strong>Capacidade hospitalar </strong><strong style="color:green">Bom</strong> (maior que 60 dias)
#                     ou Insatisfatório (entre 30 e 60 dias), indicando que o sistema de saúde tem capacidade de ser reorganizado
#                     antes de atingir capacidade, caso haja um crescimento inesperado no número de casos.</li>
#             </ul>
#         Dizemos que município está no <strong style="color:orange">Nível de Risco MÉDIO</strong> se satisfizer todos os seguintes requisitos:<br><br>
#             <ul>
#                 <li><strong>Ritmo de contágio </strong><strong style="color:green">Bom</strong> (< 1.0), mas com <strong>Subnotificação</strong> <strong style="color:orange">Insatisfatório</strong>
#                     (entre 50 e 70%), pois pode ser que o ritmo de contágio seja apenas reflexo de testagem insuficiente.
#                 </li>
#                 <li><strong>Ritmo de contágio</strong> <strong style="color:orange">Insatisfatório</strong> (< 1.0), mas com <strong>Subnotificação</strong> <strong style="color:green">Bom</strong>
#                     (< 50%), pois o ritmo de contágio ainda está elevado.
#                 </li>
#                 <li><strong>Ritmo de contágio em tendência </strong><strong style="color:orange"> estável</strong> <strong> ou</strong>
#                      </strong><strong style="color:green">queda</strong>, indicando que esperamos que o ritmo de contágio não retomará
#                      uma trajetória ascendente;</li>
#                 <li><strong>Capacidade hospitalar </strong><strong style="color:green">Bom</strong> (maior que 60 dias)
#                     ou Insatisfatório (entre 30 e 60 dias), indicando que o sistema de saúde tem capacidade de ser reorganizado
#                     antes de atingir capacidade, caso haja um crescimento inesperado no número de casos.</li>
#             </ul>
#         Dizemos que município está no <strong style="color:red">Nível de Risco ALTO</strong> se satisfizer <b>algum</b> dos seguintes requisitos:<br><br>
#             <ul>
#                 <li><strong>Ritmo de contágio </strong> <strong style="color:red">Ruim</strong> (Rt > 1.2),
#                     indicando que ainda há um crescimento exponencial da doença na cidade ou estado;</li>
#                 <li><strong>Ritmo de contágio em tendência </strong><strong style="color:red"> subindo</strong>, indicando que esperamos
#                     que o ritmo de contágio esteja atualmente maior do que o reportado;</li>
#                 <li><strong>Subnotificação </strong><strong style="color:red">Ruim</strong>  (> 70%), indicando que esperamos haver um número de
#                     infectados maior do que o registrado;</li>
#                 <li><strong>Capacidade hospitalar </strong><strong style="color:red">Ruim</strong> (< 30 dias), indicando que não há
#                     tempo de reação para evitar o colapso do sistema de saúde</li>
#             </ul>
#         Caso o município não conte com algum dos indicadores, mostramos o número correspondente para o nível estatal.
#         Nesse caso, ele não terá classificação de risco. <br><br>
#         Confira abaixo a distribuição dos municípios e estados brasileiros de acordo com os diferentes indicadores. <br><br>
#     </span>
#     """,
#         unsafe_allow_html=True,
#     )

#     st.subheader("Essas métricas são suficientes?")

#     st.write(
#         """
#         <span>
#             <b>Não.</b> Desenvolvemos os níveis de risco do FarolCovid com informações disponíveis online. É um primeiro passo para o
#             gestor orientar sua tomada de decisão de maneira informada, orientado por dados que o atualizam tanto sobre o estágio
#             de evolução da doença em seu estado ou município quanto sua capacidade de resposta. <br><br>
#             O gestor público, entretanto, conta com uma riqueza maior de informações que deve ser utilizada na formulação de respostas
#             adequadas à sua realidade. Informações como a quantidade de testes realizados, a taxa de pessoas que testam positivo e o tempo
#             médio de internação são outros fatores importantes para a tomada de decisão. Estamos à disposição para apoiar o gestor público
#             a aprofundar a análise para seu estado ou município, de forma inteiramente gratuita. Entre em contato pelo Coronacidades.org! <br><br>
#         </span>
#         """,
#         unsafe_allow_html=True,
#     )

#     st.subheader("Detalhes da distribuição dos indicadores-chave")

#     st.write(
#         """
#         Para ilustrar as classificações dos indicadores, geramos os gráficos das distribuições de cada indicador (diagonal)
#         e as distribuições por pares de indicadores (em cada eixo) abaixo, para cidades e estados.<br><br>
#         """,
#         unsafe_allow_html=True,
#     )

#     st.image(
#         Image.open("imgs/cities_indicators.png"),
#         use_column_width=True,
#         caption="Distribuição de indicadores-chaves para cidades (retrato de 26/mai/2020). Cada ponto representa uma cidade, os eixos x e y trazem os valores dos indicadores-chaves para aquela cidade. Na diagonal segue o histograma do indicador-chave.",
#     )

#     st.write("<br><br>", unsafe_allow_html=True)

#     st.image(
#         Image.open("imgs/states_indicators.png"),
#         use_column_width=True,
#         caption="Distribuição de indicadores-chaves para estados (retrato de 26/mai/2020). Cada ponto representa uma estado, os eixos x e y trazem os valores dos indicadores-chaves para aquela cidade. Na diagonal segue o histograma do indicador-chave.",
#     )

#     st.write("<br><br>", unsafe_allow_html=True)

#     st.subheader("Referências e inspirações")
#     st.write(
#         """
#         <span>
#          [1] Rio Grande do Sul, <a href="https://distanciamentocontrolado.rs.gov.br/">Modelo de Distanciamento Controlado</a><br>
#          [2] <a href="https://covidactnow.org/">COVID ActNow</a><br>
#          [3] <a href="https://blog.covidactnow.org/modeling-metrics-critical-to-reopen-safely/">A Dashboard to Help America Open Safely</a>
#          </span>
#         """,
#         unsafe_allow_html=True,
#     )


# if __name__ == "__main__":
#     main()
