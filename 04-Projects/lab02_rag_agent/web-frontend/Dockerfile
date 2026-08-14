# 第一阶段：编译构建 Node 24 镜像
FROM node:24-alpine AS build-stage
WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# 第二阶段：生产部署 Nginx 镜像
FROM nginx:alpine AS production-stage

# 复制编译后的 dist 目录到 Nginx 托管目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制 Nginx 配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
