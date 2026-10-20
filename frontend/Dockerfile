FROM node:26-alpine AS build

WORKDIR /app
RUN npm i -g corepack@0.36.0 && corepack enable
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build


FROM caddy:2.11-alpine
COPY --from=build /app/dist /srv
