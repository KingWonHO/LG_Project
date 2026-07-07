# build
FROM node:20-alpine AS build
WORKDIR /app
# package-lock.json은 복사하지 않는다 (Windows에서 생성된 lock이 리눅스 rollup 옵셔널 의존성
# 버그를 유발: @rollup/rollup-linux-x64-musl 누락. npm cli #4828). 컨테이너 안에서 새로 설치.
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
