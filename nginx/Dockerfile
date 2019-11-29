FROM nginx:1.15.0-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY ./static /public/static
COPY nginx.conf /etc/nginx/conf.d
