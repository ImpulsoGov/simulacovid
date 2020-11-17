import streamlit as st
import pandas as pd
from utils import make_clickable
import amplitude
import utils


def main(session_state):
    # Amplitude: Get user info
    user_analytics = amplitude.Amplitude_user()
    user_analytics.gen_user(utils.get_server_session())
    user_analytics.safe_log_event(
        "opened model", session_state, is_new_page=True
    )

    st.write("v1.4 - Atualizações")
    st.subheader("Inicialização dos estados")

    st.write(
        """
        Nosso modelo de projeção da capacidade hospitalar estima 2 tipos de demandas baseadas na
        intensidade da infecção: **casos severos (I2) e casos críticos (I3)**. Como ponto de partida do modelo,
        determinamos qual o percentual de casos severos e críticos dentre o total de casos ativos - já
        ajustados pela taxa de subnotificação conforme definimos anteriormente (ver Inicialização dos
        estados em v1.2). 
        
        Devido à mudança no cálculo de subnotificação, passamos a estimar casos
        assintomáticos dentre o total de casos ativos e consideramos também a distribuição etária da
        população na definição dos percentuais considerados para a inicialização. Conforme o levantamento de
        parâmetros de referência de Alison Hill (2020), cerca de 30% dos casos totais são assintomáticos.
        Dentre os 70% restantes, passamos a calcular o percentual de hospitalizados severos (I2 / I) e
        críticos (I3 / I) estimando a proporção esperada de hospitalizações na região/estado (I2+I3 / I).
        
        A proporção esperada de hospitalizações é dada pela estimativa de hospitalizações de cada faixa, de
        Verity, Robert, et al. (2020) num amplo estudo com base em 3.665 casos na China, ponderado pelo
        total da população em cada faixa etária (População residente em 2019 - CNES). Esse valor nos fornece
        o percentual total de hospitalizações esperadas na população (I2+I3/I). Para obter o percentual por
        intensidade do caso, mantivemos a razão entre severos (I2) e críticos (I3) constante: antes tínhamos
        12.5% severos e 2.5% críticos do total de casos ativos (I) - ou seja, uma razão de 0.2 críticos
        para cada caso severo (I3/I2) -, que passa a ser de 83.3% severos (I2) e 16.7% críticos (I3) do total estimado
        de hospitalizados (I2+I3 / I).  Alteramos ainda a categoria “Ventiladores” para “Leitos UTI” - testamos utitlizar 
        a nova categoria do CNES de leitos "UTI-Covid Adulto” e “UTI-Covid Infantil” porém muitas regionais 
        não possuiam dados (~30%). A taxa de contágio utilizada nos diferentes cenários segue a nova
        metodologia da Taxa de Contágio descrita nos indicadores dos Níveis de Alerta.
        """
    )

    st.header("Limitações atualizadas do modelo")

    st.write(
        """
        - O modelo trata cada cidade como um sistema fechado. Ou seja, não há mobilidade ou
          transmissão entre cidades. Também não modelamos a entrada simultânea de múltiplas pessoas
          infectadas no sistema fechado.  Além disso, tratamos todos os casos como igualmente
          capazes de infectar outras pessoas suscetíveis, não modelando a existência de
          "super-disseminadores".
        - Esta é uma doença nova. Portanto, parâmetros que modelam sua dinâmica de infecção e
          transmissão são ainda preliminares e podem mudar com o tempo. Faremos um esforço contínuo
          de atualização desses parâmetros para o melhor conhecimento científico. A velocidade de
          transmissão e a dinâmica de progressão da doença entre brasileiros podem estar sub ou
          superestimados. Os resultados da simulação devem ser interpretados de acordo.
        - Os números básicos de reprodução estimados para cada cenário são meramente fictícios, não
          estão atrelados diretamente a nenhuma intervenção que dobre ou diminua pela metade o valor
          observado hoje. Não esperamos, portanto, uma equivalência perfeita com a situação
          brasileira.  Os dados do número de leitos e leitos UTI são atualizados mensalmente
          no DATASUS CNES e há conhecidos problemas de reporte.
        - Os dados do número de casos confirmados em cada município reportados pelas secretarias
          estaduais de saúde frequentemente refletem metodologia distinta do que aqueles reportados
          pelo próprio município. Adicionalmente, existe um lag temporal entre o reporte em boletins
          epidemiológicos, a atualização no Brasil.io e o input do novo dado em nossa ferramenta.
          Sugerimos que o usuário ajuste esse parâmetro na hora de realizar a simulação.
        - A análise não considera o desenvolvimento de medidas de mitigação como vacinas e
          medicamentos anti-virais.
        """
    )

    st.write("v1.3 - Atualizações")

    st.subheader("Ritmo de contágio (**Rt**)")

    st.write(
        """
      Nessa atualização do SimulaCovid alteramos a seleção de diferentes estratégias de intervenção para a 
      seleção de *diferentes cenários de evolução da doença, a partir de hoje, dada a situação de seu município ou estado*. 
      Essa evolução é dada pelo *ritmo de contágio* estimado, que traduz quantas pessoas em média um contaminado infecta. 
      O ritmo de contágio é atualizado diariamente de acordo com o número de novos casos do município ou estado 
      (veja o cálculo desse indicador em *Estimando Ritmo de Contágio*). Os diferentes cenários para simulação são:

        - Cenário Estável: cenário no qual o ritmo de contágio da simulação é o mesmo do atual;
        - Cenário Negativo: cenário no qual o ritmo de contágio da simulação é o *dobro* do atual;
        - Cenário Positivo: cenário no qual o ritmo de contágio da simulação é a *metade* do atual;
      """
    )

    st.subheader("Capacidade Hospitalar (Oferta)")

    st.write(
        """
      Dada a evolução do Covid nos município e estados brasileiros desde a versão anterior da metodologia, 
      e a resposta dos governos com a construção e obtenção de novos recursos hospitalares, 
      modificamos também o percentual de leitos e ventiladores SUS e não-SUS disponíveis para a Covid de 20\% para 50\%.
      
      Os leitos disponíveis para Covid considerados são os tipos de leitos cirúrgicos, clínicos e hospital-dia. 
      Atualizamos os dados de leitos e ventiladores com base na última versão do DataSUS de abril/2020. 
      """
    )

    st.write("v1.2")

    st.write(
        """
        Aqui explicamos o cálculo básico por trás do SimulaCovid, além das
        fontes dos dados e modelos utilizados para estimar demanda e oferta por
        equipamentos hospitalares. Os resultados da simulação não devem ser
        usados como previsões exatas do número de casos, hospitalizações ou
        pacientes com Covid-19 que necessitarão de tratamento intensivo.

        Utilizamos cinco tipos de dados:
        - Informações sobre o número de casos e mortes confirmadas em cada
          município;
        - Informações sobre a capacidade instalada do sistema de saúde em cada
          município;
        - Informações demográficas de cada município;
        - Informações sobre a transmissão da doença, coletadas da literatura;
        - Informações sobre o impacto das diferentes políticas públicas,
          coletadas da literatura.

        """
    )

    st.subheader("Cálculo básico")

    st.write(
        """
        O SimulaCovid calcula em quantos dias a demanda de pacientes com
        Covid-19 por leitos hospitalares ($$l$$) e ventiladores ($$v$$) atingirá
        a capacidade alocada para recebê-los em cada cidade ou Região de Saúde
        no país. Portanto, estimamos tanto a oferta quanto a demanda para cada
        um dos equipamentos, $$e$$. 


        A demanda por equipamento $$e$$ ($$\mathcal{D^e(t)}$$) é dada pelo número de
        casos severos e críticos em $$t$$, estimado por meio de de um modelo
        epidemiológico. A oferta $$e$$ ($$\mathcal{O^e(t)}$$) é determinada pelo
        número de equipamentos que o município tem a disposição para pacientes
        de Covid-19. Ela também é dinâmica pois os municípios estão, por
        exemplo, instalando novos leitos e remanejando cirurgias. 


        A capacidade hospitalar é atingida quando ($$\mathcal{D^e(t)}$$) =
        ($$\mathcal{O^e(t)}$$). Logo, buscamos obter o menor  $$t$$ em dias no
        qual essa igualdade é satisfeita.
        """
    )

    st.latex("t^* = min \{t [dias] : \mathcal{D}^e(t) = \mathcal{O}^e(t)\}")

    st.write(
        """
        A demanda é uma função dos estados populacionais ($$\mathcal{P}$$),
        parâmetros da doença ($$\mathcal{D}$$) e parâmetros da reação do governo
        e sociedade ($$\mathcal{G}$$) portanto, $$\mathcal{D^e}(\mathcal{P},
        \mathcal{D}, \mathcal{G}, t)$$. Os estados populacionais dependem da
        população do município e qual estágio de contágio está a doença. Os
        parâmetro da doença dizem respeito à transmissibilidade e ao tempo de
        progressão dos diferentes estágios da doença. Os parâmetros de reação do
        governo e sociedade são relacionados às políticas públicas implementadas
        e o quanto a população adere às mesmas, ao tempo e à amplitude de
        testagem, taxa de subnotificação e cobertura da vacinação. Por exemplo,
        a transmissibilidade da doença pode variar de acordo com o nível de
        medida de restrição de contato adotada pelas diferentes esferas
        governamentais. O número básico de reprodução ($$R_0$$), em especial, é
        dependente da transmissibilidade da doença e, portanto, é impactado
        diretamente pela reação do governo e da sociedade.

        Portanto, neste exercício, variamos ($$R_0$$) de acordo com a estratégia
        de medida de restrição escolhida. Os valores foram baseados em
        estimativas do número básico de reprodução da SARS-COV-2 em Wuhan, na
        China, e sua variação conforme autoridades públicas mudavam sua
        abordagem (Wang et. al, 2020)[1]. Assim, ao permitir simular a adoção dessas
        estratégias em diferentes dias - em um espaço de até 3 meses - podemos
        projetar diferentes curvas de demanda de equipamentos hospitalares no
        município ou Região de Saúde.

        As próximas duas seções, Capacidade Hospitalar e Modelo Epidemiológico,
        apresentam os modelos para a oferta e demanda de equipamentos
        hospitalares. Finalmente, a seção Fontes de Dados mostra de onde
        extraímos os dados e como estamos nos organizando para atualizar a
        oferta de equipamentos hospitalares.
        """
    )

    st.header("Capacidade Hospitalar (Oferta)")

    st.write(
        """
        Os equipamentos hospitalares que consideramos para esse exercício são os
        ventiladores e leitos hospitalares. 

        - **Leitos**

        A quantidade de leitos por municípios soma tanto leitos hospitalares da
        rede do Sistema Único de Saúde quanto da rede não-SUS. Avaliamos que
        ambas estariam envolvidas no esforço de resposta à crise. Para usar por
        base apenas a rede SUS, seria necessário filtrar a população
        SUS-dependente de cada município.

        O número de leitos utilizado inclui leitos complementares. Retiramos os
        de tratamento intensivo, já que nossa medida de possibilidade de
        adaptação para essa modalidade são os equipamentos. 

        Consideramos, na simulação inicial, que apenas $20\%$ dos leitos
        registrados no Cadastro Nacional de Estabelecimentos Hospitalares
        estariam disponíveis para alocação de pacientes da Covid-19 que
        necessitem de internação. Esse número está dentro do parâmetro
        recomendado pela Agência Nacional de Saúde Suplementar (ANS), de
        manutenção da taxa de ocupação de hospitalar entre $75\%$ e $85\%$,
        ainda que saibamos que há grande variação nesse percentual nas
        realidades locais de cada município (ANS, 2012).

        Caso um percentual maior ou menor esteja alocado para pacientes com
        Covid-19, é possível ajustar a quantidade de leitos alocados para a
        simulação.

        - **Ventiladores**

        O número de ventiladores informado no DATASUS não traz uma distinção
        entre aqueles instalados na rede SUS ou não-SUS. Foram incluídos
        portanto todos os ventiladores.


        Vale ressaltar que não utilizamos o número de leitos já instalados como
        Unidades de Tratamento Intensivo pois entendemos que o gargalo para
        expansão da capacidade desse tipo de atendimento será a disponibilidade
        desse equipamento.
        """
    )

    st.header("Quantidade de internações (Demanda)")

    st.write(
        """
        A ferramenta utiliza uma variação do modelo epidemiológico SEIR para
        estimar a demanda por leitos hospitalares e ventiladores nos municípios
        brasileiros de pacientes com Covid-19. Permitimos a simulação do impacto
        de 3 estratégias de contenção da transmissão na sociedade, baseados na
        resposta do governo e da sociedade.

        Cada estratégia está associada a um número básico de reprodução distinto
        da Covid-19 (aproximadamente o número de novas pessoas infectadas por
        uma pessoa que já está doente). As taxas foram estimadas pelo estudo de
        Wang et. al (2020)[1] da evolução da transmissão em Wuhan, na China, sob
        diferentes políticas de restrição de contato, protocolos de tratamento e
        de testagem. Assim, ao indicar quando cada uma entrará em vigor no
        município selecionado, é possível simular a evolução da doença associada
        à sequência de estratégias indicada.
        """
    )

    st.subheader("Sobre o modelo")

    st.write(
        """
        Utilizamos o modelo epidemiológico SEIR (Suscetíveis, Expostos, Infectados e
        Removidos) adaptado segundo o modelo desenvolvido por Hill (2020) para
        calcular a disseminação e evolução clínica do COVID-19. De acordo com esse
        modelo, uma população é dividida em diferentes estados populacionais, grupos
        mutuamente excludentes de indivíduos:

        - Suscetíveis ($S$): aqueles que não têm imunidade à doença, estes se tornam
        expostos à doença a uma taxa $\\beta_i$ devido ao contato com indivíduos
        infetados $I_i$;

        - Expostos ($E$): aqueles que entram em contato com a doença e desenvolvem
        ou não sintomas, mas ainda não transmitem infecção. Esses indivíduos
        expostos progridem para o primeiro estágio de infecção ($I_1$), leve, a
        uma taxa $\sigma$.

        - Infectados ($I$): são aqueles que desenvolvem sintomas e transmitem a
        doença a uma taxa $\\beta_i$. Os casos de infecção são separados em
        diferentes estágios de gravidade:
        - Leve ($I_1$): aquele que não necessita de hospitalização, progride para
            o estado severo a uma taxa $p_1$, ou se recupera a uma taxa $\gamma_1$;
        - Severo ($I_2$): aquele que necessita de hospitalização, progride para o
            estado crítico a uma taxa $p_1$, ou se recupera a uma taxa $\gamma_2$;
        - Grave ($I_3$): aquele que além de hospitalização, necessita de
            tratamento intensivo com equipamento de ventiladores. Chegando ao caso
            grave, o indivíduo pode se recuperar a uma taxa $\gamma_3$ ou o quadro
            pode levar à morte com uma taxa $\mu$;

        - Recuperados ($R$): aqueles que, após o curso da doença, se recuperam e
        desenvolvem imunidade - não retornam ao estado suscetível.
        - Mortos ($D$): indivíduos que morrem pelo agravamento da infecção.
        """
    )

    pic = open("imgs/model_graph", "r").read()
    st.image(pic, use_column_width=True, caption=None)
    st.write("*Fonte: [Alison Hill](https://alhill.shinyapps.io/COVID19seir/)*")

    st.write(
        "Conforme a descrição acima, o conjunto de equações que determina a dinâmica do modelo é dado por:"
    )
    st.latex("\\frac{dS}{dt} = - (β_1 I_1 + β_2 I_2 + β_3 I_3) S")
    st.latex("\\frac{dE}{dt} = (β_1 I_1 + β_2 I_2 + β_3 I_3) S - \sigma E")
    st.latex("\\frac{dI_1}{dt} = \sigma E - (γ_1 + p_1) I_1")
    st.latex("\\frac{dI_2}{dt} = p_1 I_1 - (γ_2 + p_2) I_2")
    st.latex("\\frac{dI_3}{dt} = p_2 I_2 - (γ_3 + μ) I_3")
    st.latex("\\frac{dR}{dt} = γ_1 I_1 + γ_2 I_2 + γ_3 I_3")
    st.latex("\\frac{dD}{dt} = μ I_3")

    st.subheader("Parâmetros da doença")

    st.write("- **Número básico de reprodução ($$R_0$$)**")
    st.write(
        """
        O número básico de reprodução da doença nos remete ao número médio de
        pessoas que uma pessoa doente consegue infectar. Esse é um número
        característico da doença, que costuma ser estimado de forma retroativa
        conforme sua transmissão avança. Para simular diferentes estratégias,
        utilizamos $$R_0$$s estimados para a evolução da transmissão da
        SARS-Cov-2 em Wuhan, na China, conforme reportado em (Wang et. al, 2020)[1], 
        calculado para cada medida adotada pelo governo local.
        """
    )

    st.write("- **Taxas de progressão ($p_i, \\sigma$) e mortalidade ($\\mu$)**")
    st.write(
        """
        As taxas de progressão da doença representam o grau no qual um indivíduo
        avança nos estados de infecção da doença. Inicialmente, um indivíduo
        exposto avança para o primeiro estado de infeção, leve ($I_1$) a uma
        taxa $\\sigma$. Uma vez infectado, o indivíduo progride para estados
        mais graves da doença a uma taxa $p_1$ - de leve para severo - e $p_2$ -
        de severo para crítico. Assume-se que a infecção avança gradualmente, ou
        seja, uma infeção leve deve passar pelo estado severo para chegar ao
        crítico. Por fim, os casos críticos acarretam na morte de indivíduos a
        uma taxa $\\mu$.
        """
    )

    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1wvg1KFWZp4WhYVI4Gw_82bL_je_2WZHNLCcSnx95MTI/gviz/tq?tqx=out:csv&sheet=Taxas_de_progressao"
    )
    df.index = ["" for i in range(len(df))]
    st.table(df)
    st.write("- **Taxas de recuperação ($\\gamma_i$)**")
    st.write(
        """
        As taxas de recuperação da doença representam o grau no qual um
        indivíduo se recupera em qualquer estado de gravidade. Assume-se que,
        uma vez recuperado, esse indivíduo não contrai mais a doença, não
        retornando ao estado de suscetível.
        """
    )

    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1wvg1KFWZp4WhYVI4Gw_82bL_je_2WZHNLCcSnx95MTI/gviz/tq?tqx=out:csv&sheet=Taxas_de_recuperacao"
    )
    df.index = ["" for i in range(len(df))]
    st.table(df)

    st.write("- **Taxas de transmissão ($\\beta_i$)**")
    st.write(
        """
        As taxas de transmissão dizem respeito ao potencial de infecção de
        indivíduos infectados em contato a indivíduos suscetíveis. Para casos
        severos ($\\beta_2$) e críticos ($\\beta_3$), as taxas de transmissão
        desses indivíduos são referentes à transmissão interna nos hospitais, de
        pacientes para profissionais da saúde. Segundo estudos realizados na
        China e Itália (Wang et. al, 2020 [2]), esse grupo é afetado de forma
        desproporcional, sendo observado cerca de $5\%$ e $10\%$ de
        profissionais da saúde dentre o total de casos notificados,
        respectivamente. 

        Calculamos esses valores através da equação da taxa de reprodução básica
        de Hill (2020), assumindo que apenas $10\%$ do valor do $R_0$ deve-se a
        transmissões de infectados severvos ou críticos(refente a $\\beta_2,
        \\beta_3$) e que infectados severos transmitem a uma mesma taxa de
        infectados críticos, ambos hospitalizados ($\\beta_2 = \\beta_3$).
        """
    )

    st.latex(
        "R_0  = N\\frac{\\beta_1}{p_1+\gamma_1} + N\\frac{p_1}{p_1 + \gamma_1} \left( \\frac{\\beta_2}{p_2+\gamma_2} + \\frac{p_2}{p_2 + \gamma_2} \\frac{\\beta_3}{\mu+\gamma_3}\\right)"
    )

    st.write("- **Cálculo das taxas**")

    st.write(
        """
        As taxas não são observadas diretamente. Logo, utilizamos parâmetros
        observados na literatura para o cálculo das mesmas. Os parâmetros de
        referência são descritos na tabela abaixo.
        """
    )

    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1wvg1KFWZp4WhYVI4Gw_82bL_je_2WZHNLCcSnx95MTI/export?format=csv"
    ).fillna(
        "-"
    )  # .set_index('Descrição', drop=True)
    df.index = ["" for i in range(len(df))]
    st.table(df)
    st.subheader("Parâmetros da Reação da Sociedade e Governo")

    st.write(
        """
        - **Taxa de notificação ($$\\alpha$$)**

        Ainda não temos relatórios sobre a subnotificação de casos de Covid-19
        no Brasil. Estudos consultados variam ao abordar a questão: Wang et al.
        (2020)[1] consideram subnotificação de $50\%$, enquanto  Li et al.
        (2020) calculam que apenas $14\%$ dos casos de pessoas infectadas
        foram reportados, com intervalo de confiança de $10-18\%$. Os dois
        artigos consideram que casos não-notificados não tem sintomas graves e
        que não serão hospitalizados.

        O protocolo de testagem adotado atualmente no Brasil submete a testes
        clínicos somente aquelas pessoas com sintomas graves o suficiente para
        buscarem um hospital. Além disso, há crescente documentação da falta de
        testes para todos os que chegam com suspeita de coronavírus. O protocolo
        técnico de tratamento médico é o mesmo, independente do diagnóstico
        preciso. Porém, isso quer dizer que nem todos os casos não-notificados
        no Brasil são leves ou moderados: podem haver pessoas sendo
        hospitalizadas com Covid-19 mas que não são testadas e, por isso, não
        constam no registro. Têm sido recorrentes, inclusive, relatos sobre o
        aumento atípico no número de internações por doenças respiratórias.

        A taxa de notificação ($$\\alpha$$) é um número que relaciona o total de casos reportado ($I$) com o total de casos esperado dado o número de mortes reportado ($\hat{I}$). 
        Temos alguns motivos para acreditar que há menos subnotificações sistemáticos no número de mortes reportado do que casos:
        
        - Legalmente, a causa da morte precisa ser relatada e classificada de alguma forma no Brasil;
        - As mortes ocorrem após uma progressão temporal da doença, durante a qual há tempo para identificar e confirmar se a pessoa está infectada com SARS-CoV-2. 

        Portanto, utilizamos a taxa de mortalidade esperada ($$CFR = \\text{total mortes/total casos}$$) para ajustar o número de casos tomando como verdadeiro o número de mortes. 
        A melhor estimativa da taxa de mortalidade dentre diversos estudos feita por Hill (2020) é de $2\\%$.
        Utilizamos esse valor por ser calculado com base em estudos de diferentes países, diminuindo a chance de estar suscetível a algum protocolo local.
        
        O número de infectados esperado em $t$ é então dado por $\hat{I}(t) = D(t) / CFR$. Com essa estimativa, obtemos a taxa de notificação diária em $t$, dada por $\\alpha(t) = I(t)/\hat{I}(t)$. 
        A taxa de notificação calculada para o município é dada pela média dos últimos 7 dias, buscando uma maior homogeneidade:
        """
    )

    st.latex(
        "\\alpha = \sum_{t=t_i - 7}^{t_i} \\frac{I(t)}{\hat{I}(t)}, \\text{   $t_i$ = última data de atualização dos casos}"
    )
    st.write("<br>", unsafe_allow_html=True)

    st.write(
        """
        - **Tempo de diagnóstico ($$\\tau$$)**

        O tempo de diagnóstico é o tempo entre a execução do teste até o
        resultado e a inclusão do caso entre o número oficial de confirmados
        pelo Estado. Esse tempo varia de acordo com o tipo do teste realizado, a
        capacidade do estado e de clínicas privadas de realizar testes em escala
        e se há protocolo de re-testagem. O tempo de diagnóstico é importante
        pois ele representa um ‘atraso’ com o qual  que estamos inicializando o
        modelo. Por exemplo, se o tempo de diagnóstico é de 1 semana, então os
        casos confirmados hoje, são, na verdade pacientes que estavam
        apresentando sintomas há uma semana. Dependendo do tempo de diagnóstico,
        pacientes podem estar recuperados ou mortos até a doença ser confirmada.
        Portanto, essa variável nos diz quão atualizado estão os dados com
        relação à situação real da doença no município.
        """
    )

    st.subheader("Inicialização dos estados")
    st.write(
        "Para simular a evolução da doença, determinamos os valores iniciais de cada estado populacional do modelo."
    )

    st.write(
        """
        - **Infectados (I)**: o total de infectados inicialmente é dado pela
          estimativa do número de casos ativos, $I_0$, dentre os casos
          reportados no município, ajustados pela taxa de notificação. Este
          valor pode ser modificado pelo usuário nos controles para simulação.

          Dado o tempo de progressão da doença ($\delta$), os casos ativos serão
          a soma dos novos casos reportados no intervalo $t_i - \delta$ e $t_i$,
          onde $t_i$ é o dia de início da simulação. Considerando $\delta$ como
          a soma do tempo de progressão somente dos casos severo e crítico, pois
          assumimos subnotificação dos casos leves, ainda sim podemos estar
          superestimando os casos ativos por não considerar dentre eles os
          recuperados durante esse período de progressão. Por fim, ajustamos o
          total de casos ativos pela taxa de notificação de casos do municípios.
          
          Assim, se $I^t$ é o número de novos casos reportados em $t$ e
          $$\\alpha$$ é a taxa estimada de notificação de casos no município, o
          número de casos ativos é dado por: 
          """
    )

    st.latex("I(0) = \\frac{\sum_{t=t_i - \delta}^{t_i} I^t}{\\alpha}")

    st.write(
        """  
          A partir desse total, inferimos de acordo com parâmetros reportados
          quantos casos devem ser leves ($$I_1$$), severos ($$I_2$$) e críticos
          ($$I_3$$).

          Configura-se como caso severo ou crítico aquele que necessita de
          hospitalização - o caso crítico, entretanto, necessita de tratamento
          intensivo com equipamento de ventiladores. Utilizando a atualização do
          Ministério da Saúde do Brasil lançado em 28 de março de 2020,
          consideramos que aproximadamente $14.6\%$ dos casos confirmados são
          hospitalizados (569 dos 3904 casos totais). Não há reporte oficial da
          porcentagem de casos severos e críticos para o Brasil. Portanto,
          buscamos a referência dos Estados Unidos, onde o CDC (2020) reportou
          que:

          - Aproximadamente $12\%$ dos casos diagnosticados precisam de
            internação (508 dos 4446 casos confirmados)
          - Aproximadamente $2.5\%$ dos casos diagnosticados precisam de
            tratamento intensivo (121 dos 4446)

          Justificamos o uso dessa referência pela maior proximidade do perfil
          de comorbidades e hábitos entre a população dos Estados Unidos quando
          comparado à da China, além da maior semelhança na atual fase de
          transmissão comunitária da doença e da capacidade de testagem.
          Ademais, o percentual total de casos severos e críticos deste
          país ($14.5\%$) resulta em percentual similar ao reportado pelo
          Ministério da Saúde brasileiro ($14.6\%$).

          Vale ressaltar que, nessa primeira versão, não diferenciamos taxas de
          infecção e hospitalização de acordo com estrutura etária de
          brasileiros infectados por Covid-19 por não haver esse dado
          consolidado.
        """
    )

    st.latex("I_1(0) = \\frac{\gamma_1}{\gamma_1 + p_1} I(0)")
    st.latex("I_2(0) = \\frac{\gamma_2}{\gamma_2 + p_2} I(0)")
    st.latex("I_3(0) = \\frac{\gamma_3}{\gamma_3 + \mu} I(0)")
    st.latex(
        "\\text{sendo }\\frac{\gamma_1}{\gamma_1 + p_1} + \\frac{\gamma_2}{\gamma_2 + p_2} + \\frac{\gamma_3}{\gamma_3 + \mu} = 1"
    )

    st.write(
        """
            Para municípios que não possuem casos confirmados em boletins oficiais, conforme 
            reportado no Brasil.io, simulamos os números a partir do primeiro caso. 
            Isso quer dizer que, ao selecionar unidades de análise mais altas, portanto, 
            como as regionais de saúde ou os estados, você está simulando um cenário 
            onde todos os municípios têm ao menos um caso confirmado.
        """
    )

    st.write(
        """
        - **Expostos (E)**: dado o número inicial de infectados leves ($I_1$)
          calculado acima, calculamos $E(0)$ discretizando a equação
          $\\frac{dI_1}{dt}$ em $t=1$, conforme mostrado abaixo. Dado que o
          número de casos dobra a cada 5 dias (Our World in Data, 2020), aproximamos $I_1(1)
          \\approx \sqrt[5]{2} \\times I(0) \\approx 1.15 I(0)$.
        """
    )
    # st.latex("I_1(1) - I_1(0) = \sigma E(0) - \gamma I_1(0) \\rightarrow E(0) =\\frac{ I_1(1) + (\gamma - 1)I_1(0)}{\sigma}")
    st.latex(
        "E(0) \\approx \\frac{ I(1) - I(0)}{\sigma} \\approx \\frac{0.15}{\sigma} \\times I(0)"
    )

    st.write(
        """
        - **Mortos (D)**: iniciamos esse estado com o total de mortes reportado
          pelo município com os dados do Brasil.io.

        - **Recuperados (R)**: sabendo o acumulado histórico de casos, o número
          mortes ($D$) e o número de casos ativos ($I(0)$), então $R =
          \sum_{t=t_0}^{t_i} - I(0) - D$. Como é possível o número de ativos
          estar superestimado, por construção o número de recuperados estaria
          subestimado - nos casos em que o cálculo dos recuperados não é
          consistente (negativo), assumimos $R(0) = 0$.

        - **Suscetíveis (S)**: o número de indivíduos suscetíveis inicial é dado
          pelo restante da polucação do município que não se encontra em nenhum
          dos estados acima.
        """
    )

    st.latex("S(0) = N - I(0) - E(0) - R(0) - D(0)")

    st.header("Simulação das estratégias")

    st.write(
        """
        Conforme já mencionado, a dinâmica de transmissão de doenças é impactada
        diretamente por comportamentos sociais. Políticas públicas desenhadas
        para restrição de contato, desenhadas com o objetivo de influenciar
        nesse comportamento, portanto, podem ter impacto sobre a velocidade de
        transmissão de doenças. 

        Incluímos no SimulaCovid a possibilidade de estimar a evolução da
        demanda por leitos hospitalares e ventiladores sob diferentes
        estratégias de políticas públicas, que se diferenciam pelo número básico
        de reprodução ($$R_0$$) atribuído a cada uma. As mesmas foram estimadas
        por Wang et al (2020)[1] com dados empíricos da disseminação da Covid-19 em
        Wuhan, na China, em período de um pouco mais de um mês, duração da
        primeira onda de contágio por lá, e estão dispostas na tabela abaixo:

        """
    )

    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1wvg1KFWZp4WhYVI4Gw_82bL_je_2WZHNLCcSnx95MTI/gviz/tq?tqx=out:csv&sheet=Taxas_de_reproducao"
    )  # .set_index('Descrição', drop=True)
    df.index = ["" for i in range(len(df))]
    st.table(df)

    st.write(
        """
        Ainda que haja problemas com a analogia entre dinâmicas de contágio e
        aderência a decretos públicos entre o Brasil e a China, escolhemos essa
        referência por ela ter sido calculada a partir de dados observados, não
        sendo resultante de simulação, como Ferguson et al. (2020). Essa também
        é uma análise que secciona os $$R_0$$ de acordo com as políticas públicas
        adotadas no período, possibilitando que façamos a simulação desses
        diferentes cenários para os municípios brasileiros. Entretanto, ainda
        não se tem certeza de que a mudança na velocidade da infecção da
        população se deveu apenas às mudanças políticas, embora pelo tamanho das
        intervenções isso seja muito provável.
        """
    )

    st.header("Limitações")

    st.write(
        """
        - O modelo trata cada cidade como um sistema fechado. Ou seja, não há
          mobilidade ou transmissão entre cidades. Também não modelamos a
          entrada simultânea de múltiplas pessoas infectadas no sistema fechado.
          Além disso, tratamos todos os casos como igualmente capazes de
          infectar outras pessoas suscetíveis, não modelando a existência de
          "super-disseminadores".
        - Esta é uma doença nova. Portanto, parâmetros que modelam sua dinâmica
          de infecção e transmissão são ainda preliminares e podem mudar com o
          tempo. Faremos um esforço contínuo de atualização desses parâmetros
          para o melhor conhecimento científico. A velocidade de transmissão e a
          dinâmica de progressão da doença entre brasileiros podem estar sub ou
          superestimados. Os resultados da simulação devem ser interpretados de
          acordo.
        - Os números básicos de reprodução estimados para cada uma das
          estratégias de políticas públicas foram estimados de maneira
          sequencial e em contexto específico, de Wuhan, na China. Sua tradução
          para o contexto brasileiro dependerá de fatores não estimados no
          modelo, como a existência de orientações uniformes em diferentes
          esferas do poder público. Não esperamos, portanto, uma equivalência
          perfeita com a situação brasileira. Também não sabemos se as
          estratégias têm o mesmo efeito fora da sequência adotada na cidade.
        - Os dados do número de leitos e ventiladores são atualizados
          mensalmente no DATASUS CNES e há conhecidos problemas de reporte.
        - Os dados do número de casos confirmados em cada município reportados
          pelas secretarias estaduais de saúde frequentemente refletem
          metodologia distinta do que aqueles reportados pelo próprio município.
          Adicionalmente, existe um lag temporal entre o reporte em boletins
          epidemiológicos, a atualização no Brasil.io e o input do novo dado em
          nossa ferramenta. Sugerimos que o usuário ajuste esse parâmetro na
          hora de realizar a simulação.
        - A análise não considera o desenvolvimento de medidas de mitigação como
        vacinas e medicamentos anti-virais.
        """
    )

    st.header("Fonte de Dados")
    st.write(
        """
    Os dados iniciais utilizados na ferramenta foram coletados de:
    """
    )

    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1wvg1KFWZp4WhYVI4Gw_82bL_je_2WZHNLCcSnx95MTI/gviz/tq?tqx=out:csv&sheet=Fontes"
    )

    # link is the column with hyperlinks
    df["Fonte"] = df[["URL", "Fonte"]].apply(
        lambda row: make_clickable(row["Fonte"], row["URL"]), 1
    )
    st.write(df.drop("URL", axis=1).to_html(escape=False), unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)

    # st.subheader("Programa de Embaixadores")
    # st.write(
    #     """
    #     Para esta versão, também são integrados dados atualizados enviados pelos
    #     nossos Embaixadores. Os Embaixadores serão devidamente identificados como contribuidores,
    #     exceto se o Embaixador preferir colaborar de maneira anônima

    #     **Para se tornar um embaixador, inscreva-se [aqui](https://forms.gle/iPFE7T6Wrq4JzoEw9)**
    #     """
    # )
    # st.write("<br>", unsafe_allow_html=True)

    st.header("Referências")

    st.write(
        """
        Agência Nacional de Saúde Suplementar, 2012. Taxa de Ocupação Operacional Geral. Disponível em: http://www.ans.gov.br/images/stories/prestadores/E-EFI-03.pdf

        Ministério da Saúde do Brasil, 2020. Boletim Diário. 28 mar. 2020. Disponível em: https://www.saude.gov.br/images/pdf/2020/marco/28/28.03%20-%20COVID.pdf

        CDC, 2019. Severe Outcomes Among Patients with Coronavirus Disease 2019 (COVID-19) — United States, February 12–March 16, 2020. MMWR Morb Mortal Wkly Rep. ePub: 18 March 2020. DOI: http://dx.doi.org/10.15585/mmwr.mm6912e2.

        Hill, A, 2020. Model Description. Modelling COVID-19 Spread vs Healthcare Capacity. Disponível em: https://alhill.shinyapps.io/COVID19seir/

        Li, R., Pei, S., Chen, B., Song, Y., Zhang, T., Yang, W., & Shaman, J., 2020. Substantial undocumented infection facilitates the rapid dissemination of novel coronavirus (SARS-CoV2). Science, 3221(March), eabb3221. DOI: https://doi.org/10.1126/science.abb3221

        Max Roser, Hannah Ritchie, Esteban Ortiz-Ospina and Joe Hasell (2020) - "Coronavirus Disease (COVID-19)". Published online at OurWorldInData.org. Retrieved from: 'https://ourworldindata.org/coronavirus' [Online Resource]

        Walker, P.G., Whittaker, C., Watson, O., Baguelin, M., Ainslie, K.E.C., Bhatia, S., Bhatt, S., Boonyasiri, A., Boyd, O., Cattarino, L. and Cucunubá, Z., 2020. The global impact of COVID-19 and strategies for mitigation and suppression. Imperial College London, doi: https://doi.org/10.25561/77735.

        [1] Wang, C, et al. (2020) Evolving Epidemiology and Impact of Non-pharmaceutical Interventions on the Outbreak of Coronavirus Disease 2019 in Wuhan, China. DOI: https://doi.org/10.1101/2020.03.03.20030593 e pdf de apresentação https://docs.google.com/presentation/d/1-rvZs0zsXF_0Tw8TNsBxKH4V1LQQXq7Az9kDfCgZDfE/edit#slide=id.p1
        
        [2] Wang, J., Zhou, M., & Liu, F., 2020. Reasons for healthcare workers becoming infected with novel coronavirus disease 2019 (COVID-19) in China. Journal of Hospital Infection. DOI: https://doi.org/10.1016/j.jhin.2020.03.002
        """
    )


if __name__ == "__main__":
    main(session_state=None)
