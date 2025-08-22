FROM node:18-alpine as build-stage

WORKDIR /frontend

COPY ./frontend /frontend

ENV REACT_APP_BACKEND_URL="/"

RUN yarn install && yarn build


FROM python:3.11-slim

ENV STATIC_INDEX 1
ENV CONFIG_DIR "/config"

# Install Python dependencies
COPY ./backend/requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend code
COPY ./backend /app

# Copy frontend build
COPY --from=build-stage /frontend/build /app/static

# Create config directory
RUN mkdir -p $CONFIG_DIR

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Starting Flask app..."\n\
cd /app && FLASK_APP=main python3 -m flask run --host=0.0.0.0 --port=80' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 80

CMD ["/app/start.sh"]
