FROM node:10 as build-stage

WORKDIR /frontend

COPY ./frontend /frontend

ENV REACT_APP_BACKEND_URL="/"

RUN yarn install && yarn build


FROM tiangolo/uwsgi-nginx-flask:python3.7

ENV STATIC_INDEX 1

COPY ./backend /app

COPY --from=build-stage /frontend/build /app/static
COPY --from=build-stage /frontend/build/static/css /app/static/css
COPY --from=build-stage /frontend/build/static/js /app/static/js

RUN pip install -r /app/requirements.txt
