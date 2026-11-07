"""Interface gráfica (CustomTkinter) da Calculadora Geodésica."""
import math
import os
import sys

import customtkinter as ctk

# permite executar este ficheiro directamente (a pasta raiz do projecto passa a estar no caminho)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geodesia import CATALOGO, Elipsoide, puissant, sodano, coordenadas, utm, reducoes
from geodesia.utils import ler_angulo, ler_numero, formatar_dms

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONTE_MONO = ("Consolas", 13)
COR_ERRO = "#e5534b"
LIMITE_PUISSANT_M = 100_000.0
METODOS = ["Puissant", "Sodano", "Comparar"]
AVISO_PUISSANT = "⚠ Puissant é indicado para linhas até ~100 km; acima disso os erros crescem rapidamente."


class Card(ctk.CTkFrame):
    """Cartão com título, campos de entrada, botão e caixa de resultado."""

    def __init__(self, master, titulo, campos, botao, comando, altura_saida=210):
        super().__init__(master, corner_radius=14)
        self.entradas = {}
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text=titulo, font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=18, pady=(16, 8), sticky="w")
        linha = 1
        for chave, rotulo, dica in campos:
            ctk.CTkLabel(self, text=rotulo, anchor="w").grid(row=linha, column=0, padx=(18, 10), pady=5, sticky="w")
            entrada = ctk.CTkEntry(self, placeholder_text=dica)
            entrada.grid(row=linha, column=1, padx=(0, 18), pady=5, sticky="ew")
            entrada.bind("<Return>", lambda _e: comando(self))
            self.entradas[chave] = entrada
            linha += 1
        ctk.CTkButton(self, text=botao, command=lambda: comando(self)).grid(
            row=linha, column=0, columnspan=2, padx=18, pady=(10, 8), sticky="ew")
        self.saida = ctk.CTkTextbox(self, height=altura_saida, font=FONTE_MONO, wrap="none")
        self.saida.grid(row=linha + 1, column=0, columnspan=2, padx=18, pady=(0, 18), sticky="nsew")
        self.grid_rowconfigure(linha + 1, weight=1)
        self._cor_normal = ctk.ThemeManager.theme["CTkTextbox"]["text_color"]
        self.saida.configure(state="disabled")

    def texto(self, chave):
        return self.entradas[chave].get()

    def angulo(self, chave):
        return ler_angulo(self.texto(chave))

    def numero(self, chave):
        return ler_numero(self.texto(chave))

    def mostrar(self, texto, erro=False):
        self.saida.configure(state="normal", text_color=COR_ERRO if erro else self._cor_normal)
        self.saida.delete("1.0", "end")
        self.saida.insert("1.0", texto)
        self.saida.configure(state="disabled")


def seguro(funcao):
    """Mostra erros de entrada no cartão em vez de rebentar a aplicação."""
    def interno(self, card):
        try:
            funcao(self, card)
        except (ValueError, ZeroDivisionError, OverflowError) as erro:
            card.mostrar(f"Erro: {erro}", erro=True)
    return interno


def _ponto(lat, lon):
    return (f"  φ = {formatar_dms(lat, 'lat')}   ({lat:.9f}°)\n"
            f"  λ = {formatar_dms(lon, 'lon')}   ({lon:.9f}°)")


def _bloco_directo(nome, r):
    return (f"{nome}\n  φ₂ = {formatar_dms(r.lat2, 'lat')}   ({r.lat2:.9f}°)\n"
            f"  λ₂ = {formatar_dms(r.lon2, 'lon')}   ({r.lon2:.9f}°)\n"
            f"  Az₂₋₁ = {formatar_dms(r.az21)}   ({r.az21:.7f}°)")


def _bloco_inverso(nome, r):
    return (f"{nome}\n  s₁₋₂ = {r.s:,.4f} m   ({r.s / 1000:,.6f} km)\n"
            f"  Az₁₋₂ = {formatar_dms(r.az12)}   ({r.az12:.7f}°)\n"
            f"  Az₂₋₁ = {formatar_dms(r.az21)}   ({r.az21:.7f}°)")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora Geodésica")
        self.geometry("1220x780")
        self.minsize(1040, 700)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._barra_lateral()
        self._abas()
        self._actualizar_info()

    # ------------------------------------------------------------------ layout
    def _barra_lateral(self):
        barra = ctk.CTkFrame(self, width=250, corner_radius=0)
        barra.grid(row=0, column=0, sticky="nsew")
        barra.grid_propagate(False)
        ctk.CTkLabel(barra, text="🌍  Geodésica", font=ctk.CTkFont(size=24, weight="bold")).pack(
            padx=20, pady=(28, 2), anchor="w")
        ctk.CTkLabel(barra, text="Calculadora de Geodesia Geométrica", text_color=("gray35", "gray65"),
                     wraplength=210, justify="left").pack(padx=20, pady=(0, 24), anchor="w")

        ctk.CTkLabel(barra, text="Elipsoide", anchor="w", font=ctk.CTkFont(weight="bold")).pack(padx=20, anchor="w")
        self.var_elipsoide = ctk.StringVar(value="WGS84")
        self.menu_elip = ctk.CTkOptionMenu(barra, values=list(CATALOGO) + ["Personalizado"],
                                           variable=self.var_elipsoide, command=self._ao_mudar_elipsoide)
        self.menu_elip.pack(padx=20, pady=(6, 10), fill="x")

        self.quadro_pers = ctk.CTkFrame(barra, fg_color="transparent")
        self.ent_a = ctk.CTkEntry(self.quadro_pers, placeholder_text="a (m)")
        self.ent_invf = ctk.CTkEntry(self.quadro_pers, placeholder_text="1/f")
        self.ent_a.pack(fill="x", pady=3)
        self.ent_invf.pack(fill="x", pady=3)
        ctk.CTkButton(self.quadro_pers, text="Aplicar", height=28, command=self._actualizar_info).pack(fill="x", pady=3)

        self.lbl_info = ctk.CTkLabel(barra, text="", justify="left", anchor="w", font=FONTE_MONO)
        self.lbl_info.pack(padx=20, pady=(8, 0), anchor="w")
        self._barra = barra

        ctk.CTkLabel(barra, text="Aparência", anchor="w", font=ctk.CTkFont(weight="bold")).pack(
            padx=20, pady=(28, 0), anchor="w")
        tema = ctk.CTkSegmentedButton(barra, values=["Escuro", "Claro"], command=self._mudar_tema)
        tema.set("Escuro")
        tema.pack(padx=20, pady=(6, 0), fill="x")

        ctk.CTkLabel(barra, text="Ângulos: aceita 25.9692,\n-25 58 9.12  ou  25°58'9.12\" S",
                     text_color=("gray35", "gray65"), justify="left").pack(side="bottom", padx=20, pady=20, anchor="w")

    def _abas(self):
        abas = ctk.CTkTabview(self, corner_radius=14)
        abas.grid(row=0, column=1, sticky="nsew", padx=16, pady=(8, 16))
        nomes = ["Ângulos", "Geodésicas ⇄ Cartesianas", "UTM", "Problema Directo", "Problema Inverso", "Reduções e Alturas"]
        for n in nomes:
            abas.add(n)
            abas.tab(n).grid_columnconfigure((0, 1), weight=1, uniform="col")
            abas.tab(n).grid_rowconfigure(1, weight=1)

        t = abas.tab("Ângulos")
        Card(t, "Converter ângulo (DD ⇄ DMS)", [("v", "Ângulo", "ex.: -25.9692  ou  25 58 9.12 S")],
             "Converter", self.calc_angulo).grid(row=1, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")

        t = abas.tab("Geodésicas ⇄ Cartesianas")
        Card(t, "(φ, λ, h)  →  (X, Y, Z)",
             [("lat", "Latitude φ", "ex.: -25.9692"), ("lon", "Longitude λ", "ex.: 32.5732"), ("h", "Altitude h (m)", "0")],
             "Calcular X, Y, Z", self.calc_geo_xyz).grid(row=1, column=0, padx=8, pady=8, sticky="nsew")
        Card(t, "(X, Y, Z)  →  (φ, λ, h)",
             [("x", "X (m)", ""), ("y", "Y (m)", ""), ("z", "Z (m)", "")],
             "Calcular φ, λ, h", self.calc_xyz_geo).grid(row=1, column=1, padx=8, pady=8, sticky="nsew")

        t = abas.tab("UTM")
        Card(t, "Geodésicas  →  UTM",
             [("lat", "Latitude φ", "ex.: -25.9692"), ("lon", "Longitude λ", "ex.: 32.5732"),
              ("zona", "Zona (opcional)", "automática se vazio")],
             "Converter para UTM", self.calc_geo_utm).grid(row=1, column=0, padx=8, pady=8, sticky="nsew")
        Card(t, "UTM  →  Geodésicas",
             [("zona", "Zona", "ex.: 36"), ("hemi", "Hemisfério", "N ou S"), ("e", "Este E (m)", ""), ("n", "Norte N (m)", "")],
             "Converter para φ, λ", self.calc_utm_geo).grid(row=1, column=1, padx=8, pady=8, sticky="nsew")

        t = abas.tab("Problema Directo")
        self.met_dir = self._seletor_metodo(t)
        Card(t, "Dados: P₁, Az₁₋₂ e s₁₋₂",
             [("lat", "Latitude φ₁", "ex.: -25.9692"), ("lon", "Longitude λ₁", "ex.: 32.5732"),
              ("az", "Azimute Az₁₋₂", "graus ou G M S"), ("s", "Distância s (m)", "ex.: 50000")],
             "Calcular P₂", self.calc_directo).grid(row=1, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")

        t = abas.tab("Problema Inverso")
        self.met_inv = self._seletor_metodo(t)
        Card(t, "Dados: P₁ e P₂",
             [("lat1", "Latitude φ₁", ""), ("lon1", "Longitude λ₁", ""),
              ("lat2", "Latitude φ₂", ""), ("lon2", "Longitude λ₂", "")],
             "Calcular s, Az₁₋₂, Az₂₋₁", self.calc_inverso).grid(row=1, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")

        t = abas.tab("Reduções e Alturas")
        rolagem = ctk.CTkScrollableFrame(t, fg_color="transparent")
        rolagem.grid(row=1, column=0, columnspan=2, sticky="nsew")
        rolagem.grid_columnconfigure((0, 1), weight=1, uniform="col")
        cartoes = [
            ("Inclinada → horizontal (zenital z)", [("S", "S (m)", ""), ("z", "Zenital z", "graus ou G M S")],
             "Calcular", self.calc_zenital),
            ("Inclinada → horizontal (vertical v)",
             [("S", "S (m)", ""), ("v", "Vertical v", "graus ou G M S"), ("i", "Altura instr. i (m)", "0"), ("p", "Altura prisma p (m)", "0")],
             "Calcular", self.calc_vertical),
            ("Redução ao elipsóide", [("dh", "Dh (m)", ""), ("H", "Altitude H (m)", ""), ("R", "Raio R (m)", "ex.: 6371000")],
             "Calcular D₀", self.calc_elipsoide),
            ("Factor de escala", [("d0", "D₀ ou D_grelha (m)", ""), ("k", "Factor k", "ex.: 0.9998")],
             "Calcular", self.calc_escala),
            ("Nivelamento geométrico",
             [("a", "Leituras atrás a", "valores separados por ;"), ("f", "Leituras à frente f", "valores separados por ;"),
              ("ha", "Cota inicial H_A", "opcional"), ("ref", "Desnível conhecido", "opcional (erro de fecho)")],
             "Calcular ΔH", self.calc_nivelamento),
            ("Alturas h ≈ H + N", [("N", "Ondulação N (m)", ""), ("h", "Elipsoidal h (m)", "deixe vazio se calcular h"),
                                   ("Hh", "Ortométrica H (m)", "deixe vazio se calcular H")],
             "Calcular", self.calc_alturas),
            ("Coordenadas a partir de azimute",
             [("ea", "E_A (m)", ""), ("na", "N_A (m)", ""), ("d", "Distância D (m)", ""), ("az", "Azimute A", "graus ou G M S")],
             "Calcular B", self.calc_coord_az),
            ("Azimute e distância entre dois pontos",
             [("ea", "E_A (m)", ""), ("na", "N_A (m)", ""), ("eb", "E_B (m)", ""), ("nb", "N_B (m)", "")],
             "Calcular D e A", self.calc_az_dist),
        ]
        for n, (titulo, campos, botao, cmd) in enumerate(cartoes):
            Card(rolagem, titulo, campos, botao, cmd, altura_saida=90).grid(
                row=n // 2, column=n % 2, padx=8, pady=8, sticky="nsew")

    def _seletor_metodo(self, aba):
        quadro = ctk.CTkFrame(aba, fg_color="transparent")
        quadro.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 0))
        ctk.CTkLabel(quadro, text="Método:").pack(side="left", padx=(0, 10))
        botao = ctk.CTkSegmentedButton(quadro, values=METODOS)
        botao.set("Sodano")
        botao.pack(side="left")
        return botao

    # ------------------------------------------------------------- elipsoide
    def _ao_mudar_elipsoide(self, valor):
        if valor == "Personalizado":
            self.quadro_pers.pack(padx=20, fill="x", after=self.menu_elip)
        else:
            self.quadro_pers.pack_forget()
        self._actualizar_info()

    def elipsoide(self):
        if self.var_elipsoide.get() == "Personalizado":
            return Elipsoide.personalizado(ler_numero(self.ent_a.get()), inv_f=ler_numero(self.ent_invf.get()))
        return CATALOGO[self.var_elipsoide.get()]

    def _actualizar_info(self):
        try:
            e = self.elipsoide()
            self.lbl_info.configure(
                text=f"a   = {e.a:,.3f} m\nb   = {e.b:,.3f} m\n1/f = {e.inv_f:.9f}\ne²  = {e.e2:.12f}")
        except ValueError as erro:
            self.lbl_info.configure(text=f"Elipsoide inválido:\n{erro}")

    def _mudar_tema(self, valor):
        ctk.set_appearance_mode("dark" if valor == "Escuro" else "light")

    # --------------------------------------------------------------- cálculos
    @seguro
    def calc_angulo(self, card):
        dd = card.angulo("v")
        card.mostrar(f"Graus decimais : {dd:.10f}°\nG M S           : {formatar_dms(dd)}\n"
                     f"Radianos        : {math.radians(dd):.12f}\nGrados          : {dd * 10 / 9:.8f} gon")

    @seguro
    def calc_geo_xyz(self, card):
        e = self.elipsoide()
        h = card.numero("h") if card.texto("h").strip() else 0.0
        X, Y, Z = coordenadas.geodesicas_para_cartesianas(e, card.angulo("lat"), card.angulo("lon"), h)
        card.mostrar(f"X = {X:,.4f} m\nY = {Y:,.4f} m\nZ = {Z:,.4f} m")

    @seguro
    def calc_xyz_geo(self, card):
        e = self.elipsoide()
        lat, lon, h = coordenadas.cartesianas_para_geodesicas(e, card.numero("x"), card.numero("y"), card.numero("z"))
        card.mostrar(f"{_ponto(lat, lon)}\n  h = {h:,.4f} m")

    @seguro
    def calc_geo_utm(self, card):
        e = self.elipsoide()
        zona = int(card.numero("zona")) if card.texto("zona").strip() else None
        z, h, E, N = utm.geodesicas_para_utm(e, card.angulo("lat"), card.angulo("lon"), zona)
        card.mostrar(f"Zona         : {z}{h}\nMeridiano C. : {utm.meridiano_central(z):.0f}°\n"
                     f"E = {E:,.3f} m\nN = {N:,.3f} m")

    @seguro
    def calc_utm_geo(self, card):
        e = self.elipsoide()
        lat, lon = utm.utm_para_geodesicas(e, int(card.numero("zona")), card.texto("hemi"),
                                           card.numero("e"), card.numero("n"))
        card.mostrar(_ponto(lat, lon))

    @staticmethod
    def _dif_metros(e, lat, a, b):
        """Diferença horizontal (m) entre duas posições (lat, lon) próximas."""
        phi = math.radians(lat)
        w = math.sqrt(1 - e.e2 * math.sin(phi) ** 2)
        M, N = e.a * (1 - e.e2) / w ** 3, e.a / w
        return math.hypot(math.radians(b[0] - a[0]) * M, math.radians(b[1] - a[1]) * N * math.cos(phi))

    @seguro
    def calc_directo(self, card):
        e = self.elipsoide()
        lat1, lon1, az, s = card.angulo("lat"), card.angulo("lon"), card.angulo("az"), card.numero("s")
        if s < 0:
            raise ValueError("A distância deve ser positiva.")
        metodo = self.met_dir.get()
        partes = []
        if metodo in ("Puissant", "Comparar"):
            rp = puissant.directo(e, lat1, lon1, az, s)
            partes.append(_bloco_directo("PUISSANT", rp))
        if metodo in ("Sodano", "Comparar"):
            rs = sodano.directo(e, lat1, lon1, az, s)
            partes.append(_bloco_directo("SODANO", rs))
        if metodo == "Comparar":
            d = self._dif_metros(e, lat1, (rp.lat2, rp.lon2), (rs.lat2, rs.lon2))
            partes.append(f"Diferença horizontal de P₂ (Puissant − Sodano): {d:,.4f} m")
        if metodo != "Sodano" and s > LIMITE_PUISSANT_M:
            partes.append(AVISO_PUISSANT)
        card.mostrar("\n\n".join(partes))

    @seguro
    def calc_inverso(self, card):
        e = self.elipsoide()
        lat1, lon1, lat2, lon2 = (card.angulo(k) for k in ("lat1", "lon1", "lat2", "lon2"))
        metodo = self.met_inv.get()
        partes = []
        if metodo in ("Puissant", "Comparar"):
            rp = puissant.inverso(e, lat1, lon1, lat2, lon2)
            partes.append(_bloco_inverso("PUISSANT", rp))
        if metodo in ("Sodano", "Comparar"):
            rs = sodano.inverso(e, lat1, lon1, lat2, lon2)
            partes.append(_bloco_inverso("SODANO", rs))
        if metodo == "Comparar":
            partes.append(f"Diferença de distância (Puissant − Sodano): {rp.s - rs.s:,.4f} m")
        ref = rs.s if metodo != "Puissant" else rp.s
        if metodo != "Sodano" and ref > LIMITE_PUISSANT_M:
            partes.append(AVISO_PUISSANT)
        card.mostrar("\n\n".join(partes))

    @staticmethod
    def _lista(texto):
        partes = [x for x in texto.replace(",", ".").split(";") if x.strip()]
        if not partes:
            raise ValueError("Indique pelo menos um valor.")
        return [float(x) for x in partes]

    @seguro
    def calc_zenital(self, card):
        dh, dv = reducoes.inclinada_zenital(card.numero("S"), card.angulo("z"))
        card.mostrar(f"Dh = {dh:,.3f} m\nΔh = {dv:,.3f} m")

    @seguro
    def calc_vertical(self, card):
        i = card.numero("i") if card.texto("i").strip() else 0.0
        p = card.numero("p") if card.texto("p").strip() else 0.0
        dh, dv, dH = reducoes.inclinada_vertical(card.numero("S"), card.angulo("v"), i, p)
        card.mostrar(f"Dh = {dh:,.3f} m\nΔh = {dv:,.3f} m\nΔH (= Δh + i − p) = {dH:,.3f} m")

    @seguro
    def calc_elipsoide(self, card):
        d0 = reducoes.reduzir_ao_elipsoide(card.numero("dh"), card.numero("H"), card.numero("R"))
        card.mostrar(f"D₀ = {d0:,.3f} m\nRedução = {d0 - card.numero('dh'):,.3f} m")

    @seguro
    def calc_escala(self, card):
        d, k = card.numero("d0"), card.numero("k")
        g = reducoes.distancia_grelha(d, k)
        card.mostrar(f"D_grelha = k·D₀ = {g:,.3f} m (diferença {g - d:,.3f} m)\n"
                     f"D₀ = D_grelha/k = {reducoes.distancia_elipsoide_de_grelha(d, k):,.3f} m")

    @seguro
    def calc_nivelamento(self, card):
        ha = card.numero("ha") if card.texto("ha").strip() else None
        ref = card.numero("ref") if card.texto("ref").strip() else None
        dh, hf, erro = reducoes.circuito_nivelamento(self._lista(card.texto("a")), self._lista(card.texto("f")), ha, ref)
        txt = f"ΔH = Σa − Σf = {dh:,.3f} m"
        if hf is not None:
            txt += f"\nH_B = {hf:,.3f} m"
        if erro is not None:
            txt += f"\nErro de fecho = {erro:,.3f} m"
        card.mostrar(txt)

    @seguro
    def calc_alturas(self, card):
        N = card.numero("N")
        if card.texto("h").strip():
            card.mostrar(f"H ≈ h − N = {reducoes.altura_ortometrica(card.numero('h'), N):,.3f} m")
        elif card.texto("Hh").strip():
            card.mostrar(f"h ≈ H + N = {reducoes.altura_elipsoidal(card.numero('Hh'), N):,.3f} m")
        else:
            raise ValueError("Preencha h ou H.")

    @seguro
    def calc_coord_az(self, card):
        dE, dN, EB, NB = reducoes.coordenadas_por_azimute(card.numero("ea"), card.numero("na"),
                                                          card.numero("d"), card.angulo("az"))
        card.mostrar(f"ΔE = {dE:,.3f} m   ΔN = {dN:,.3f} m\nE_B = {EB:,.3f} m\nN_B = {NB:,.3f} m")

    @seguro
    def calc_az_dist(self, card):
        d, a = reducoes.azimute_distancia(card.numero("ea"), card.numero("na"), card.numero("eb"), card.numero("nb"))
        card.mostrar(f"D = {d:,.3f} m\nA = {formatar_dms(a)}   ({a:.7f}°)")
