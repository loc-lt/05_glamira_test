#!/usr/bin/env bash
# Checkpoint 4a: point gcloud at the project, enable APIs, create the VM service account.
# Billing must already be linked to the project in the console.
source "$(dirname "$0")/lib.sh"

gcloud config set project "$GCP_PROJECT_ID"
gcloud config set compute/region "$GCP_REGION"
gcloud config set compute/zone "$GCP_ZONE"

gcloud services enable \
  compute.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com \
  iam.googleapis.com

if gcloud iam service-accounts describe "$SA_EMAIL" >/dev/null 2>&1; then
  echo "service account exists: $SA_EMAIL"
else
  gcloud iam service-accounts create "$GCP_SA_NAME" --display-name="Glamira VM loader"
fi

gcloud services list --enabled --filter="name:(compute OR storage OR bigquery)" --format="value(config.name)"
