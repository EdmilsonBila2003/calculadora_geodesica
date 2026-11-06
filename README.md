# Calculadora Geodésica

Aplicação de desktop em Python puro (CustomTkinter) para a disciplina de Geodesia.
Interface moderna com tema escuro/claro, cálculos separados da interface, testes e controlo de versões com Git.

## Funções

| Separador | Cálculo |
|---|---|
| Ângulos | Graus decimais ⇄ G M S, radianos, grados |
| Geodésicas ⇄ Cartesianas | (φ, λ, h) ⇄ (X, Y, Z) |
| UTM | (φ, λ) ⇄ (zona, E, N) |
| Problema Directo | Puissant, Sodano ou comparação dos dois |
| Problema Inverso | Puissant, Sodano ou comparação dos dois |

Elipsoides: WGS84, GRS80, Clarke 1880 (RGS), Clarke 1866, Bessel 1841, Internacional 1924, Krassovsky 1940 e personalizado (a, 1/f).
Os ângulos aceitam `-25.9692`, `-25 58 9.12` ou `25°58'9.12" S`.

## Como executar (VS Code)

1. `File > Open Folder` e escolher esta pasta.
2. Criar o ambiente virtual e activá-lo:
   ```
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   source .venv/bin/activate       # Linux / macOS
   ```
3. `pip install -r requirements.txt`
4. `python main.py`

Requer Python 3.10 ou superior com tkinter (já incluído no instalador oficial para Windows).

## Testes

```
python -m unittest discover -s tests -v
```

Os resultados de Puissant e Sodano são comparados com a solução de Vincenty (`tests/referencia_vincenty.py`, usada só como referência).

## Estrutura

```
main.py                    ponto de entrada
geodesia/elipsoides.py     elipsoides e parâmetros derivados (f, e², e'², n)
geodesia/utils.py          leitura/formatação de ângulos, tipos de resultado
geodesia/coordenadas.py    geodésicas ⇄ cartesianas
geodesia/utm.py            UTM
geodesia/puissant.py       problemas directo e inverso de Puissant
geodesia/sodano.py         problemas directo e inverso de Sodano
ui/app.py                  janela, cartões e abas (CustomTkinter)
tests/                     testes unitários e referência de Vincenty
```

## Git

```
git log --oneline
git switch -c nome-da-funcionalidade
git add . && git commit -m "mensagem"
```
Os commits iniciais usam uma identidade genérica. Configure a sua com
`git config user.name "O seu nome"` e `git config user.email "o_seu@email"`.

## Notas sobre as fórmulas do PDF (importante)

Ao validar o código contra Vincenty, algumas equações do PDF `Formulas_Geodesia.pdf` davam resultados errados
(provavelmente erros de transcrição). O código segue o PDF excepto nos pontos abaixo; confirme-os com o seu docente ou com a fonte original.

| Eq. | PDF | Código | Motivo |
|---|---|---|---|
| 10 (Puissant) | 3.º termo com factor `B` | sem `B` | `B` é dimensionalmente incoerente; com `B` o resultado muda 0,7–2,5 m a 100 km |
| 31 (Puissant) | `R = arctan(x/y) + γ/2` | `Az₁₋₂ = arctan(x/y) − γ/2` | coerente com a Eq. 33 (`Az + γ/2` é o azimute médio); este sinal reproduz Vincenty |
| 42 e 73 (Sodano) | `m₁ = k·(1 − cos β₀)` | `m₁ = k·(1 − cos² β₀)` | com `cos β₀` sem quadrado o erro chega a quilómetros em linhas de 5000 km |
| 66 (Sodano) | termo `m²·(−f²/16)·φ` | `m²·(+f²/16)·φ` | deduzido a partir do arco de meridiano e confirmado numericamente |
| 55 (Sodano) | série para B₂ | `tan B₂ = tan β₂ / (1 − f)` (Eq. 53) | relação exacta; a Eq. 55 aparece truncada no PDF |
| 46 / 77 (Sodano) | `cot α₂₋₁` com φ₀ ou φ | `atan2` / fórmula esférica com λ | evita divisão por zero em meridianos; a versão do inverso com φ dava erros de ~1″ |

O azimute `α₂₋₁` devolvido é o azimute de 2 para 1 (azimute directo em 2 mais 180°).

## Precisão medida (WGS84, contra Vincenty)

| Método | Linha | Erro de distância | Erro de azimute |
|---|---|---|---|
| Puissant inverso | 30–95 km | ≤ 0,36 m | ≤ 0,15″ |
| Puissant directo | ≤ 100 km | ≤ 0,06 m | < 0,01″ |
| Puissant | ~700 km | ~65 m (inverso), ~13 m (directo) | ~27″ |
| Sodano inverso | 30–95 km | ≤ 0,003 m | ≤ 0,3″ |
| Sodano inverso | 700–8700 km | ≤ 0,25 m | ≤ 0,3″ |
| Sodano directo | ≤ 700 km | ≤ 0,01 m | < 0,01″ |
| Sodano directo | 8000 km | ~10 m | ~0,14″ |

Puissant só deve ser usado até cerca de 100 km (a interface avisa). Sodano não foi testado para pontos antípodas.

## Limitações

- UTM só entre 80°S e 84°N, sem as zonas especiais da Noruega e Svalbard.
- Verifique os parâmetros dos elipsoides com o material da disciplina (valores da literatura corrente).
- A janela foi testada apenas em lógica (ver abaixo); o aspecto visual deve ser confirmado no seu computador.
