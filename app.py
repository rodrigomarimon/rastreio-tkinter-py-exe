'''
Esta versão usa somente tkinter, sem flask, e apos inserir os dados na interface, abre um navegador com o mapa
Nesta versão, não é necessário ter o arquivo no diretório nem mencionar o arquivo dentro do código, pois abre uma aba para escolher qual arquivo deseja usar
melhoras a fazer: validar entrada de dados, melhorar botão de escolha do arquivo csv, transformar em .exe após melhorias 
'''

import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
import subprocess
import tkinter as tk
from tkinter import filedialog
import os
import re
from datetime import datetime

df = pd.DataFrame()
intervalo_minutos = 4

def validar_data(data):
    # Aceita datas nos formatos YYYY-MM-DD ou DD/MM/YYYY ou DD-MM-YYYY ou DDMMYYYY
    formatos_data = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d%m%Y']
    for formato in formatos_data:
        try:
            datetime.strptime(data, formato)
            return True
        except ValueError:
            pass
    return False

def validar_hora(hora):
    # Aceita horas nos formatos HH:MM:SS ou HHMMSS
    formato_hora = ['%H:%M:%S', '%H%M%S']
    for formato in formato_hora:
        try:
            datetime.strptime(hora, formato)
            return True
        except ValueError:
            pass
    return False

def carregar_dataframe_csv(caminho):
    try:
        df = pd.read_csv(caminho, encoding='ISO-8859-1')
        # print(df)

        df['DataHora'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], format='%d/%m/%Y %H:%M:%S')
        df['Latitude'] = df['Latitude'].str.replace(',', '.').astype(float)
        df['Longitude'] = df['Longitude'].str.replace(',', '.').astype(float)
        # print(df)

        if 'DataHora' not in df.columns:
            raise ValueError("O arquivo CSV não contém a coluna DataHora.")
        return df
    except Exception as e:
        print(f'Erro ao carregar arquivo CSV: {e}')
        return pd.DataFrame()

def criar_mapa(df_filtrado):
    mapa = folium.Map(location=[df_filtrado.iloc[0]['Latitude'], df_filtrado.iloc[0]['Longitude']], zoom_start=14)

    df_velocidade_zero = df_filtrado[df_filtrado['Velocidade'] == 0]
    dados_heatmap = df_velocidade_zero[['Latitude', 'Longitude']].values.tolist()

    HeatMap(dados_heatmap).add_to(mapa)
    tempo_anterior = None

    for _, row in df_filtrado.iterrows():
        if tempo_anterior is None or (row['DataHora'] - tempo_anterior).seconds >= intervalo_minutos * 60:
            latitude, longitude = row['Latitude'], row['Longitude']
            google_maps_link = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
            popup_content = f"{row['Placa']} - {row['Data']} {row['Hora']} - Velocidade: {row['Velocidade']} km/h - LatLong: {[latitude, longitude]}<br><a href='{google_maps_link}' target='_blank'>Ver no Google Maps</a>"

            marker = folium.Marker(location=[latitude, longitude],
                                  popup=folium.Popup(popup_content, max_width=300)
                                  ).add_to(mapa)

            tempo_anterior = row['DataHora']

    # Use um caminho relativo para salvar o mapa
    mapa.save('mapa_deslocamento.html')
    path = 'mapa_deslocamento.html'

    # Abra o arquivo HTML no navegador padrão
    try:
        os.startfile(path)
    except AttributeError:
        subprocess.Popen(['open', path], shell=True)

def criar_mapa_da_interface():
    file_path = filedialog.askopenfilename(filetypes=[("Arquivos CSVs", "*.csv")])
    if file_path:
        global df
        df = carregar_dataframe_csv(file_path)

        data_inicial = entry_data_inicial.get()
        hora_inicial = entry_hora_inicial.get()
        data_final = entry_data_final.get()
        hora_final = entry_hora_final.get()

        if not all([data_inicial, hora_inicial, data_final, hora_final]):
            print("Forneça todas datas e horas")
            return

        # Remova os separadores das datas e horas fornecidas
        data_inicial_sem_separadores = re.sub(r'[^0-9\-]', '', data_inicial)
        data_final_sem_separadores = re.sub(r'[^0-9\-]', '', data_final)
        hora_inicial_sem_separadores = re.sub(r'[^0-9:]', '', hora_inicial)
        hora_final_sem_separadores = re.sub(r'[^0-9:]', '', hora_final)
        print(data_final_sem_separadores, data_inicial_sem_separadores, hora_final_sem_separadores, hora_inicial_sem_separadores)
        if not validar_data(data_inicial_sem_separadores) or not validar_data(data_final_sem_separadores):
            print("Formato de data inválido. Use YYYY-MM-DD ou DD/MM/YYYY ou DD-MM-YYYY ou DDMMYYYY")
            return

        if not validar_hora(hora_inicial_sem_separadores) or not validar_hora(hora_final_sem_separadores):
            print("Formato de hora inválido. Use HH:MM:SS ou HHMMSS")
            return
        if df.empty:
            print("Carrege um arquivo CSV primeiro")
            return

        filtro = ((df['DataHora'] >= pd.to_datetime(f'{data_inicial} {hora_inicial}', format='%Y-%m-%d %H:%M:%S')) &
                  (df['DataHora'] <= pd.to_datetime(f'{data_final} {hora_final}', format='%Y-%m-%d %H:%M:%S')))
        df_filtrado = df[filtro].copy()

        if df_filtrado.empty:
            print(f"Não há dados no intervalo de datas especificado: {data_inicial} {hora_inicial} - {data_final} {hora_final}")
            return
        print(f"Intervalo de datas e horas fornecido: {data_inicial} - {data_final}")

        criar_mapa(df_filtrado)

# Layout da interface gráfica
root = tk.Tk()
root.title("Configuração de datas e horas")

tk.Label(root, text="Selecione o arquivo CSV:").pack(pady=10)
tk.Button(root, text="Carregar CSV", command=criar_mapa_da_interface).pack(pady=10)

tk.Label(root, text="Data Inicial (AAAA-MM-DD):").pack(pady=5)
entry_data_inicial = tk.Entry(root)
entry_data_inicial.pack(pady=5)

tk.Label(root, text="Hora Inicial (HH:MM:SS):").pack(pady=5)
entry_hora_inicial = tk.Entry(root)
entry_hora_inicial.pack(pady=5)

tk.Label(root, text="Data Final (AAAA-MM-DD):").pack(pady=5)
entry_data_final = tk.Entry(root)
entry_data_final.pack(pady=5)

tk.Label(root, text="Hora Final (HH:MM:SS):").pack(pady=5)
entry_hora_final = tk.Entry(root)
entry_hora_final.pack(pady=5)

tk.Button(root, text="Criar Mapa", command=criar_mapa_da_interface).pack(pady=20)

root.mainloop()
