terraform {
  required_version = ">= 1.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# Image Docker de l'application (construite par le pipeline).
resource "docker_image" "app" {
  name         = var.image_name
  keep_locally = true
}

# Conteneur de staging provisionne par Terraform.
resource "docker_container" "staging" {
  name  = var.container_name
  image = docker_image.app.image_id

  ports {
    internal = 8000
    external = var.app_port
    ip       = "0.0.0.0"
  }

  # Le reseau cicd-network est cree en amont (docker compose / pipeline).
  networks_advanced {
    name = var.network_name
  }

  healthcheck {
    test     = ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
    interval = "30s"
    timeout  = "10s"
    retries  = 3
  }
}
