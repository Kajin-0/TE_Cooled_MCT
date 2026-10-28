# amd64 Ubuntu 24.04; isolated from the Ubuntu 25.10 host.
FROM ubuntu:24.04@sha256:78d4744ead1f5b19b04d0df558ab182a5300903900755e515b2ca4d10eb2044d
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake gfortran libblas-dev liblapack-dev libglu1-mesa \
    python3-venv ca-certificates curl git \
    && dpkg-query -W > /opt/apt-packages.lock && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir \
    numpy==2.1.3 scipy==1.14.1 matplotlib==3.9.2 meshio==5.3.5 \
    gmsh==4.13.1 pytest==8.3.4 setuptools==75.6.0 wheel==0.45.1
ARG ELMER_COMMIT=a19504ac53ec222e3355e182b08f2ff280c2203a
RUN curl -fLsS https://codeload.github.com/ElmerCSC/elmerfem/tar.gz/${ELMER_COMMIT} -o /tmp/elmer.tar.gz \
    && mkdir /tmp/elmer-src && tar -xzf /tmp/elmer.tar.gz -C /tmp/elmer-src --strip-components=1 \
    && cmake -S /tmp/elmer-src -B /tmp/elmer-build \
       -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/elmer \
       -DWITH_ELMERGUI=FALSE -DWITH_ELMERPOST=FALSE -DWITH_MPI=FALSE \
       -DWITH_OpenMP=FALSE -DWITH_ElmerIce=FALSE -DWITH_LUA=FALSE \
    && cmake --build /tmp/elmer-build -j4 \
    && cmake --install /tmp/elmer-build \
    && mkdir -p /opt/elmer/provenance \
    && cp /tmp/elmer-src/fem/src/modules/ThermoElectricSolver.F90 /opt/elmer/provenance/ \
    && cp -r /tmp/elmer-src/fem/tests/ThermoElectric /opt/elmer/provenance/upstream-test \
    && echo ${ELMER_COMMIT} > /opt/elmer/provenance/commit \
    && rm -rf /tmp/elmer-src /tmp/elmer-build /tmp/elmer.tar.gz
# The headless Gmsh wheel still dynamically links the OpenGL runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libxrender1 libxcursor1 libxfixes3 libxft2 libfontconfig1 libxinerama1 \
    && dpkg-query -W > /opt/apt-packages.lock && rm -rf /var/lib/apt/lists/*
ENV PATH="/opt/elmer/bin:/opt/venv/bin:${PATH}" \
    ELMER_HOME=/opt/elmer \
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg
WORKDIR /work
