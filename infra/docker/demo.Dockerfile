FROM node:20-alpine
WORKDIR /app
COPY apps/demo/package.json /app/
RUN corepack enable && corepack prepare pnpm@9.6.0 --activate && pnpm install
COPY apps/demo /app
EXPOSE 8085
CMD ["pnpm","preview","--host","0.0.0.0"]
