FROM nginx:alpine

# Copy index.html
COPY index.html /usr/share/nginx/html/index.html.template

# Expose port 80
EXPOSE 80

# Replace URL and start nginx
# We use 'exec' to make nginx the PID 1 process
CMD ["/bin/sh", "-c", "envsubst '${BACKEND_URL}' < /usr/share/nginx/html/index.html.template > /usr/share/nginx/html/index.html && exec nginx -g 'daemon off;'"]
