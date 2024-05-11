FROM node:12 as build-stage

WORKDIR /frontend

COPY ./frontend /frontend

ENV REACT_APP_BACKEND_URL="/"

RUN yarn install && yarn build


FROM tiangolo/uwsgi-nginx-flask:python3.10

ENV STATIC_INDEX 1
ENV CONFIG_DIR "/config"

COPY ./backend/requirements.txt/ /app
RUN pip install -r /app/requirements.txt
COPY ./backend /app

COPY --from=build-stage /frontend/build /app/static
COPY --from=build-stage /frontend/build/static/css /app/static/css
COPY --from=build-stage /frontend/build/static/js /app/static/js
RUN mkdir -p $CONFIG_DIR

# copied from here: https://github.com/se1exin/Cleanarr/issues/135#issuecomment-2091709103
RUN echo "buffer-size=32768" >> /app/uwsgi.ini
