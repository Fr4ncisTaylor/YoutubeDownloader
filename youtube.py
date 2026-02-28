import yt_dlp as youtube_dl
import os
from pprint import pprint

# Função para garantir que o diretório existe
def criar_diretorio(destino):
    if not os.path.exists(destino):
        os.makedirs(destino)

def listar_resolucoes(url):
    ydl_opts = {}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formatos = info_dict.get('formats', [])
        
        # Mostra detalhes do vídeo
        detalhes = {
            'titulo': info_dict.get('title', 'Desconhecido'),
            'capa': info_dict.get('thumbnail', 'Sem capa'),
            'duração': info_dict.get('duration', 'Desconhecida'),
            'autor': info_dict.get('uploader', 'Desconhecido'),
            'descrição': info_dict.get('description', 'Sem descrição'),
            'formatos': formatos
        }
        
        return detalhes
      
def baixar_video_melhor_resolucao(url):
    # Define o caminho para a pasta "youtudown" dentro de "Documentos"
    caminho_documentos = os.path.join(os.path.expanduser("~"), "Documents", "youtudown")
    
    # Cria o diretório se ele não existir
    criar_diretorio(caminho_documentos)
    
    # Define as opções para o youtube_dl, incluindo o diretório de download e a melhor qualidade
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Baixa a melhor qualidade disponível (vídeo + áudio)
        'outtmpl': os.path.join(caminho_documentos, '%(title)s.%(ext)s')  # Salva no diretório especificado
    }
    
    # Baixa o vídeo na melhor qualidade
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        print(f"Vídeo baixado na melhor resolução disponível em {caminho_documentos}")