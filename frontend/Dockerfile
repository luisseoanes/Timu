FROM node:22-alpine

WORKDIR /app
# Con el lockfile y `npm ci` la imagen instala exactamente lo mismo que CI.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
