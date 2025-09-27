FROM python:3.13.7-slim-bookworm

# Configure Environment Variable
WORKDIR /source/
ARG DISCORD_GUILD_ID
ARG DISCORD_TOKEN
ARG GTOKEN
ARG SENTRY_DSN
ARG SENTRY_ENVIRONMENT
ENV DISCORD_GUILD_ID=${DISCORD_GUILD_ID}
ENV DISCORD_TOKEN=${DISCORD_TOKEN}
ENV GTOKEN=${GTOKEN}
ENV SENTRY_DSN=${SENTRY_DSN}
ENV SENTRY_ENVIRONMENT=${SENTRY_ENVIRONMENT}

# Copy Source and setup
COPY ./src/* ./
COPY ./requirements.txt ./requirements.txt
RUN python -m pip install --upgrade -r requirements.txt

# Run Service
CMD python ./main.py