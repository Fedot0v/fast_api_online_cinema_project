FROM nginx:1.25-alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY static /app/static

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"] 