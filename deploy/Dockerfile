# Review and pin the resolved base-image digest before public deployment.
FROM python:3.11-slim-bookworm@sha256:528257d48c1da0dcecc2e725d1ae34498d60c965f1241e39cd6a85a8859bdf84
RUN apt-get update && apt-get install -y --no-install-recommends git build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir . waitress==3.0.2 && useradd --uid 10001 --create-home app
USER 10001
ENV DSF_DATA_DIR=/state DSF_OFFICIAL_WORKBOOK=/reference/official.xlsm PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/matplotlib OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
EXPOSE 8080
CMD ["python", "-m", "lic_dsf.hosted_server"]
