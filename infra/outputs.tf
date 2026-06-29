output "app_url" {
  description = "URL de l'environnement de staging provisionne."
  value       = "http://localhost:${var.app_port}"
}

output "container_id" {
  description = "Identifiant du conteneur de staging."
  value       = docker_container.staging.id
}

output "network_name" {
  description = "Nom du reseau Docker utilise par le staging."
  value       = var.network_name
}
