FROM python:3.12-slim

WORKDIR /app

# Instalar dependências do sistema (incluindo libpq para psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (cache layer)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Verificar se FastAPI foi instalado (debug)
RUN python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')" || echo "ERROR: FastAPI not installed"

# Copiar código da aplicação
COPY . .

# Criar diretórios de uploads
# NOTA: Em produção, este diretório deve ser montado como volume persistente
# Configure no Coolify: Source Path -> /root/fortunevegas-uploads, Destination Path -> /app/uploads
RUN mkdir -p uploads/logos uploads/banners uploads/promotions && \
    chmod -R 755 uploads

# Variáveis de ambiente padrão (podem ser sobrescritas no Coolify)
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV PYTHONPATH=/app

# Expor porta
EXPOSE 8000

# Verificar instalação antes de iniciar
RUN python -c "import fastapi, uvicorn, psycopg2; print('Dependencies OK')" || (echo "ERROR: Dependencies missing" && exit 1)

# Comando para iniciar a aplicação
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
