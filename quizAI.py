# Instalação
!pip install --upgrade google-generativeai ipywidgets --quiet

import google.generativeai as genai
import ipywidgets as widgets
from IPython.display import display, clear_output
import re
from google.colab import userdata

# Configuração da API Key
api_key = userdata.get('GEMINI_API_KEY')
genai.configure(api_key=api_key)

# Gera 10 perguntas apenas textuais
def gerar_perguntas(nivel, materia):
    prompt = f"""
Você é um tutor que cria quizzes educativos de texto.
Não inclua imagens ou mídias — apenas perguntas baseadas em texto.
Nível: {nivel} (dificuldade adequada).
Matéria: {materia} (conteúdo apropriado).

Instruções:
- Gere exatamente 10 questões de múltipla escolha de texto.
- Formato:
  Pergunta X: <texto>
  A) ...
  B) ...
  C) ...
  D) ...
  Resposta correta: <letra>
- Separe cada bloco com linha em branco.

Evite ambiguidade para respostas claras e unívocas.
"""
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    r = model.generate_content(prompt)
    return r.text or ''

# Extrai perguntas e alternativas
def parse_perguntas(texto):
    blocos = re.findall(r'Pergunta \d+:.*?(?=Pergunta \d+:|\Z)', texto, re.DOTALL)
    qs = []
    for b in blocos:
        p = re.search(r'Pergunta \d+:\s*(.*?)\n', b).group(1).strip()
        alts = {letra: texto.strip() for letra, texto in re.findall(r'([A-D])\)\s*(.*?)\n', b)}
        ans = re.search(r'Resposta correta:\s*([A-D])', b).group(1).upper()
        qs.append({'p': p, 'alts': alts, 'ans': ans})
    return qs

# Definições de níveis e matérias
niveis = ['Fundamental 1','Fundamental 2','Ensino Médio 1','Ensino Médio 2','Ensino Médio 3']
mats = {
    'Fundamental 1': ['Ciências','Matemática','Astronomia'],
    'Fundamental 2': ['Ciências','Matemática','Astronomia'],
    'Ensino Médio 1': ['Química','Física','Biologia','Matemática','Astronomia'],
    'Ensino Médio 2': ['Química','Física','Biologia','Matemática','Astronomia'],
    'Ensino Médio 3': ['Química','Física','Biologia','Matemática','Astronomia']
}

# Widgets iniciais
dd_n = widgets.Dropdown(options=niveis, description='Nível:')
dd_m = widgets.Dropdown(options=mats[niveis[0]], description='Matéria:')
bt_start = widgets.Button(description='Iniciar Quiz', button_style='primary')
display(dd_n, dd_m, bt_start)

# Ajusta matérias conforme nível
def on_nivel_change(change):
    dd_m.options = mats[change['new']]
dd_n.observe(on_nivel_change, names='value')

estado = {'qs': [], 'i': 0, 'score': 0}

# Inicia quiz
def iniciar(b):
    clear_output()
    texto = gerar_perguntas(dd_n.value, dd_m.value)
    qs = parse_perguntas(texto)
    estado.update(qs=qs, i=0, score=0)
    mostrar()
bt_start.on_click(iniciar)

# Exibe perguntas
def mostrar():
    clear_output()
    q = estado['qs'][estado['i']]
    print(f"{estado['i']+1}/{len(estado['qs'])}: {q['p']}")
    radios = widgets.RadioButtons(
        options=[f"{k}) {v}" for k, v in q['alts'].items()],
        description='',
        layout={'width':'auto'}
    )
    btn_r = widgets.Button(description='Responder', button_style='success', disabled=True)
    btn_n = widgets.Button(description='Próxima', button_style='info', disabled=True)
    out = widgets.Output()
    display(radios, btn_r, btn_n, out)

    radios.observe(lambda c: setattr(btn_r, 'disabled', False), names='value')

    def on_resp(_):
        with out:
            clear_output()
            escolha = radios.value.split(')')[0].strip().upper()
            correta = q['ans']
            if escolha == correta:
                print('✅ Correto!'); estado['score'] += 1
            else:
                print(f'❌ Errado! Resposta certa: {correta}) {q["alts"][correta]}')
        btn_r.disabled, radios.disabled, btn_n.disabled = True, True, False
    btn_r.on_click(on_resp)

    def on_next(_):
        estado['i'] += 1
        if estado['i'] < len(estado['qs']): mostrar()
        else: fim()
    btn_n.on_click(on_next)

# Fim do quiz
def fim():
    clear_output()
    tot, ac = len(estado['qs']), estado['score']
    pct = (ac/tot*100) if tot else 0
    print(f"Quiz finalizado! Acertos: {ac}/{tot} ({pct:.1f}%)")
    btn_reset = widgets.Button(description='Reiniciar Quiz', button_style='warning')
    btn_reset.on_click(lambda _: (clear_output(), display(dd_n, dd_m, bt_start)))
    display(btn_reset)
