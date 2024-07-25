FROM node:16.20.2-slim
WORKDIR /opt/star-burger/frontend
COPY src .
RUN npm ci --include=dev --force
# ENTRYPOINT ["./node_modules/.bin/parcel"]
# CMD ["build", "bundles-src/index.js", "--dist-dir=bundles", "--public-url='./'"]
RUN ./node_modules/.bin/parcel build bundles-src/index.js --dist-dir=bundles --public-url="./"
ENTRYPOINT ["/bin/bash"]