# Local, non-upstream compatibility image for RomM 5.4.1.
# The overlay inherits RomM's startup contract; adding USER/HEALTHCHECK would
# alter its nginx/init behavior rather than improve this compatibility patch.
# trunk-ignore-all(trivy/DS-0002,trivy/DS-0026,checkov/CKV_DOCKER_2,checkov/CKV_DOCKER_3): preserve the official RomM runtime contract
# Keep both upstream image and sigil source pinned by digest/commit.
ARG ROMM_BASE_IMAGE=rommapp/romm:5.4.1@sha256:923a808be529a834a171b3e045821aeb7e2851f4b6fc9514076785b68a9142f6
ARG PYTHON_VERSION=3.14
ARG PYTHON_ALPINE_SHA256=9e9fde4d32eedce0b661d9ab91e826b62dddf28e928c230ec55f1866cac66b01
ARG SIGIL_VERSION=0190443fe39dd72d0534db3d07bfabc5f35997a5

FROM python:${PYTHON_VERSION}-alpine3.24@sha256:${PYTHON_ALPINE_SHA256} AS sigil-build
ARG SIGIL_VERSION
WORKDIR /argosy-sigil
RUN apk add --no-cache \
    cmake=4.2.3-r0 \
    g++=15.2.0-r5 \
    git=2.54.0-r0 \
    make=4.4.1-r4 \
    musl-dev=1.2.6-r3 \
    && git clone --filter=blob:none https://github.com/rommapp/argosy-sigil.git . \
    && git checkout "${SIGIL_VERSION}" \
    && git submodule update --init --recursive \
    && cmake -B build-python -S . -DSIGIL_BUILD_CLI=OFF -DSIGIL_BUILD_TESTS=OFF \
    && cmake --build build-python --target sigil \
    && pip install --no-cache-dir cffi==2.1.1 setuptools==84.2.1 pycparser==3.12

WORKDIR /argosy-sigil/bindings/python
RUN python build_sigil.py \
    && mkdir /sigil-pkg \
    && cp sigil/*.py sigil/_sigil.*.so /sigil-pkg/

# trunk-ignore(checkov/CKV_DOCKER_7): default ARG pins the official 5.4.1 image by digest
FROM ${ROMM_BASE_IMAGE} AS romm-library-fixes
ARG PYTHON_VERSION
COPY --from=sigil-build /sigil-pkg /src/.venv/lib/python${PYTHON_VERSION}/site-packages/sigil
COPY patches/ /tmp/local-library-fixes/
RUN python3 /tmp/local-library-fixes/patch_worker.py /backend/handler/rq_worker.py \
    && python3 /tmp/local-library-fixes/patch_sigil_adapter.py /backend/adapters/services/sigil.py \
    && rm -rf /tmp/local-library-fixes
