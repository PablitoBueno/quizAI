# Notebook: Quiz Interativo com Google Gemini no Colab
"""
Instruções:
1. Abra um notebook no Google Colab.
2. No painel Secrets, crie "GEMINI_API_KEY" com sua chave.
3. Execute esta célula e as seguintes.
"""

# Instalação de dependências
!pip install --upgrade google-generativeai ipywidgets --quiet

# Imports e configuração da API
import google.generativeai as genai
import ipywidgets as widgets
from IPython.display import display, clear_output
import re
from google.colab import userdata

# Configuração da API Key
try:
    api_key = userdata.get('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
except Exception:
    print('❌ Erro ao configurar API Key')

# Funções de geração e parser de perguntas

def gerar_perguntas(nivel, materia):
    prompt = f"""
Instrução: Gere 5 perguntas de múltipla escolha.
Nível: {nivel}
Matéria: {materia}
Formato:
Pergunta X: texto
A) ...
B) ...
C) ...
D) ...
Resposta correta: <letra>
"""
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    r = model.generate_content(prompt)
    return r.text if r.parts else ''


def parse_perguntas(texto):
    blocos = re.findall(r'Pergunta \d+:.*?(?=Pergunta \d+:|\Z)', texto, re.DOTALL)
    questoes = []
    for b in blocos:
        p = re.search(r'Pergunta \d+:\s*(.*?)\n', b).group(1)
        alts = {m[0]:m[1] for m in re.findall(r'([A-D])\)\s*(.*?)\n', b)}
        cor = re.search(r'Resposta correta:\s*([A-D])', b).group(1)
        questoes.append({'pergunta': p, 'alternativas': alts, 'correta': cor})
    return questoes

# Definição de níveis e matérias
niveis = ['Fundamental 1', 'Fundamental 2', 'Ensino Médio']
materias = ['Matemática', 'História', 'Ciências']

# Widgets iniciais
dropdown_nivel = widgets.Dropdown(options=niveis, description='Nível:')
dropdown_materia = widgets.Dropdown(options=materias, description='Matéria:')
botao_iniciar = widgets.Button(description='Iniciar Quiz', button_style='primary')
display(dropdown_nivel, dropdown_materia, botao_iniciar)

# Estado do quiz
tela = {'questoes': [], 'index': 0, 'score': 0}

# Função para iniciar quiz
def iniciar_quiz(b):
    clear_output()
    nivel = dropdown_nivel.value
    materia = dropdown_materia.value
    texto = gerar_perguntas(nivel, materia)
    tela['questoes'] = parse_perguntas(texto)
    tela['index'] = 0
    tela['score'] = 0
    mostrar_questao()

botao_iniciar.on_click(iniciar_quiz)

# Função para exibir pergunta

def mostrar_questao():
    clear_output()
    q = tela['questoes'][tela['index']]
    print(f"Pergunta {tela['index']+1}/{len(tela['questoes'])}: {q['pergunta']}")
    radios = widgets.RadioButtons(options=[f"{k}) {v}" for k, v in q['alternativas'].items()])
    botao_resp = widgets.Button(description='Responder', button_style='success', disabled=True)
    botao_next = widgets.Button(description='Próxima', button_style='info', disabled=True)
    display(radios, botao_resp, botao_next)

    # Habilita botão responder ao selecionar alternativa
    radios.observe(lambda change: setattr(botao_resp, 'disabled', False), names='value')

    # Ação ao responder
    def on_responder(_):
        resposta = radios.value.split(')')[0]
        if resposta == q['correta']:
            print('✅ Correto!')
            tela['score'] += 1
        else:
            print(f"❌ Errado. A resposta certa era {q['correta']}) {q['alternativas'][q['correta']]}" )
        botao_resp.disabled = True
        radios.disabled = True
        botao_next.disabled = False

    botao_resp.on_click(on_responder)

    # Ação ao próxima
    def on_proxima(_):
        tela['index'] += 1
        if tela['index'] < len(tela['questoes']):
            mostrar_questao()
        else:
            mostrar_resultado()

    botao_next.on_click(on_proxima)

# Função para exibir resultado

def mostrar_resultado():
    clear_output()
    total = len(tela['questoes'])
    acert = tela['score']
    print(f"Quiz finalizado! Você acertou {acert}/{total} ({acert/total*100:.1f}%).")
    botao_reset = widgets.Button(description='Reiniciar Quiz')
    botao_reset.on_click(lambda _: (clear_output(), display(dropdown_nivel, dropdown_materia, botao_iniciar)))
    display(botao_reset)
