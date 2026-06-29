# Ecommerce COD & Media Buyers Metrics API

API REST de calcul de metriques e-commerce en **Cash on Delivery (COD)** et de
performance des **media buyers**. Le projet sert de support a une chaine CI/CD
complete :

`Code -> Docker -> Jenkins -> SonarQube -> Trivy -> Registry -> Terraform -> Monitoring`

## Membres du groupe

- Yassine AFIF
- Mohamed TAHIRI

> Depot Git public : `https://github.com/afif-yassine/devops_Ecomerce`

## A quoi sert l'application

L'API ingere deux types de donnees :

1. **Commandes COD** (`/orders`) : chaque commande est attribuee a un media buyer
   et possede un statut (`pending`, `confirmed`, `delivered`, `returned`, `cancelled`).
2. **Ad spend** (`/adspend`) : le budget publicitaire depense par chaque media buyer.

Elle calcule ensuite les KPIs cles du e-commerce COD :

| Metrique | Definition |
|----------|------------|
| Taux de confirmation | (confirmees + livrees) / total commandes |
| Taux de livraison | livrees / confirmees |
| ROAS | revenu livre / ad spend |
| CPA | ad spend / commandes livrees |
| Profit | revenu livre - cout des biens - ad spend |

## Endpoints

| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Liveness probe -> `{"status": "ok"}` |
| GET | `/metrics` | Metriques au format Prometheus |
| POST | `/orders` | Ingestion d'un lot de commandes COD |
| POST | `/adspend` | Ingestion d'un lot d'ad spend |
| GET | `/metrics/media-buyers` | KPIs par media buyer |
| GET | `/metrics/global` | KPIs globaux du store |
| POST | `/reset` | Vide le store en memoire (demo/tests) |

Documentation interactive : `http://localhost:8001/docs`

## Metriques Prometheus exposees (metier)

- `cod_orders_ingested_total{status="..."}` (Counter)
- `cod_adspend_ingested_total` (Counter)
- `cod_global_roas` (Gauge)
- `cod_global_confirmation_rate` (Gauge)
- `cod_global_profit` (Gauge)

## Lancer en local (sans pipeline)

```bash
# 1) Construire et lancer via docker-compose (cree le reseau cicd-network)
docker compose up -d --build

# 2) Verifier la sante
curl http://localhost:8001/health

# 3) Injecter des donnees de demo
curl -X POST http://localhost:8001/orders -H "Content-Type: application/json" -d @samples/orders.json
curl -X POST http://localhost:8001/adspend -H "Content-Type: application/json" -d @samples/adspend.json

# 4) Consulter les KPIs
curl http://localhost:8001/metrics/global
curl http://localhost:8001/metrics/media-buyers
```

## Tests et couverture

```bash
pip install -r requirements-dev.txt
pytest            # genere coverage.xml + rapport terminal
flake8 src/ tests/
```

## Monitoring (Prometheus + Grafana)

```bash
# L'application doit tourner (cicd-network cree par docker compose up).
cd monitoring
docker compose up -d
```

- Prometheus : http://localhost:9090 (cible `cod-metrics-api` en etat UP dans /targets)
- Grafana : http://localhost:3000 (admin / admin) -> dashboard "COD & Media Buyers Monitoring"

## Pipeline CI/CD (Jenkins - 9 stages)

1. **Checkout** - clone le code, affiche le SHA
2. **Lint** - flake8
3. **Build & Test** - build Docker + pytest + coverage.xml
4. **SonarQube** - analyse qualite
5. **Quality Gate** - `waitForQualityGate`
6. **Security Scan** - Trivy (CVE)
7. **Push** - publication sur ghcr.io (branche `main`)
8. **IaC Apply** - `terraform apply` (staging)
9. **Smoke Test** - `curl /health` repond 200

Le pipeline est defini dans le `Jenkinsfile` a la racine.

> Avant de lancer le pipeline : configurer les credentials Jenkins
> `ghcr-credentials` (username `afif-yassine` + Personal Access Token GitHub)
> et le serveur `sonarqube`.
