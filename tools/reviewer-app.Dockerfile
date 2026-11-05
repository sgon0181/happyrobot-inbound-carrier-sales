FROM node:22-bookworm-slim
WORKDIR /app
COPY ops-app/package.json ops-app/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY --chown=node:node ops-app/ ./
RUN chown node:node /app
USER node
ENV NODE_ENV=development NEXT_TELEMETRY_DISABLED=1
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
