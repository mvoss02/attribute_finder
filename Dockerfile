FROM python:3.11-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Pakete für SQL Server und ODBC Treiber installieren
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    locales \
    locales-all \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Deutsch als Locale für korrekte Zeitstempel setzen
RUN sed -i '/de_DE.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

# ODBC Treiber für SQL Server installieren
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*
# SQL Server Tools installieren
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends mssql-tools \
    && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc \
    && /bin/bash -c "source ~/.bashrc" \
    && rm -rf /var/lib/apt/lists/*

# Install the project into `/app`
WORKDIR /app

# Copy the custom root certificate into the container
COPY SonicWALL_Firewall_DPI-SSL.crt /usr/local/share/ca-certificates/SonicWALL_Firewall_DPI-SSL.crt

# Update the certificate store
RUN update-ca-certificates


# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy
ENV UV_NATIVE_TLS=1

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --native-tls

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --native-tls && \
    uv pip install "fastapi[standard]" --native-tls

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []
EXPOSE 8000
# Run the FastAPI application by default
# Uses `uvicorn` to run the FastAPI app
CMD ["uvicorn", "src.api.api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]