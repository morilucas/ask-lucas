FROM node:24-bookworm-slim AS dependencies
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

FROM node:24-bookworm-slim AS builder
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY apps/web ./
RUN mkdir -p public
ARG NEXT_PUBLIC_API_BASE_URL=/api
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build

FROM node:24-bookworm-slim AS runner
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000
WORKDIR /app
RUN chown node:node /app
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --from=builder --chown=node:node /app/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
