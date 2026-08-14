# 专门为低配 (1GB 内存) 服务器优化的轻量级 Nginx 镜像
FROM nginx:alpine

# 直接复制预先编译好的静态资源文件，免去服务器端耗尽内存的 npm build
COPY dist /usr/share/nginx/html

# 复制 Nginx 配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
