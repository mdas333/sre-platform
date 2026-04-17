# ADR 0003 — OpenTofu for infrastructure-as-code

Status: Accepted
Date: 2026-04-16

## Context

Terraform was relicensed under the BSL in August 2023. OpenTofu is a Linux-Foundation-governed, MPL-2.0-licensed fork based on the last open-source Terraform commit. As of January 2024 OpenTofu is considered production-ready; several large companies have migrated or begun evaluating migrations.

OpenTofu uses identical HCL syntax, the same providers (including `kreuzwerker/k3d`), and the same workflow as Terraform. Migration is a single CLI swap for most projects.

## Decision

Use OpenTofu as the infrastructure-as-code tool throughout the portfolio. State is stored locally (SQLite backend) for this project; remote state is documented as a future TODO.

## Consequences

**Upside**

- Aligns with the current open-source trajectory of the IaC ecosystem.
- Compatible with all existing Terraform providers and modules.
- Documents awareness of the 2023 license change — a relevant signal in interviews.

**Downside**

- The candidate pool of public Terraform training material is larger; OpenTofu material is catching up but smaller.
- Some third-party tools still default to `terraform` in their documentation; equivalents under `tofu` usually exist.
