from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
import json
import os

app = FastAPI(title="API Localização de Estágio")

# Configuração de CORS - em produção, recomendamos substituir "*" pelo domínio exato do Netlify
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Banco de dados em memória temporário (uma lista simples)
historico_localizacoes = []

ARQUIVO_CACHE = "dados.json"

# Carregar dados salvos ao iniciar o servidor
if os.path.exists(ARQUIVO_CACHE):
    try:
        with open(ARQUIVO_CACHE, "r", encoding="utf-8") as f:
            historico_localizacoes = json.load(f)
    except Exception as e:
        print("Erro ao carregar cache local:", e)
        historico_localizacoes = []

# Serve a página HTML na rota raiz (Visão do Aluno)
@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

# Serve o Painel com Mapa (Visão do Professor/Admin)
@app.get("/admin")
async def serve_admin():
    return FileResponse("static/admin.html")

# Endpoint para retornar todas as localizações para o mapa
@app.get("/api/localizacoes")
async def obter_localizacoes():
    return historico_localizacoes

# Modelo de dados que vamos receber
class LocalizacaoAluno(BaseModel):
    matricula: str = "Visitante"
    latitude: float
    longitude: float
    precisao_metros: float

@app.post("/api/registrar-localizacao")
async def registrar_localizacao(dados: LocalizacaoAluno, request: Request):
    # Obtém o IP do header X-Forwarded-For (usado em hospedagens como Render/Netlify) ou usa o IP da conexão direta
    ip_cliente = request.headers.get("X-Forwarded-For", request.client.host if request.client else "Desconhecido")
    if ip_cliente:
        ip_cliente = ip_cliente.split(",")[0].strip()

    hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Salvar na lista em memória para mostrar no mapa depois
    registro = {
        "matricula": dados.matricula,
        "latitude": dados.latitude,
        "longitude": dados.longitude,
        "precisao_metros": dados.precisao_metros,
        "hora": hora_atual,
        "ip": ip_cliente
    }
    historico_localizacoes.append(registro)

    # Salvar a lista atualizada no arquivo local (cache)
    try:
        with open(ARQUIVO_CACHE, "w", encoding="utf-8") as f:
            json.dump(historico_localizacoes, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print("Erro ao salvar no cache:", e)

    # Log no terminal com Link para o Google Maps
    link_google_maps = f"https://www.google.com/maps?q={dados.latitude},{dados.longitude}"
    
    print(f"[{hora_atual}] Aluno(a) matrícula: {dados.matricula} (IP: {ip_cliente}) localizado.")
    print(f"Coordenadas: {dados.latitude}, {dados.longitude} (Precisão: {dados.precisao_metros}m)")
    print(f"Mapa: {link_google_maps}")
    print("-" * 50)
    
    return {"status": "sucesso", "mensagem": "Localização registrada com sucesso"}

# Para rodar: uvicorn main:app --host 0.0.0.0 --port 8000
