FROM nginx:1.15.0-alpine

COPY ./static /public/static
COPY config.tmpl /etc/nginx/
RUN rm /etc/nginx/conf.d/default.conf

CMD /bin/sh -c "envsubst '\$SSL_CERT,\$SSL_KEY,\$PROXY_PASS_ADDRESS,\$STATIC_FOLDER' < /etc/nginx/config.tmpl \
    > /etc/nginx/conf.d/nginx.conf && exec nginx -g 'daemon off;'"