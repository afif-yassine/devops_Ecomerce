variable "image_name" {
  description = "Nom complet de l'image Docker a deployer en staging."
  type        = string
  default     = "cod-metrics-api:latest"
}

variable "container_name" {
  description = "Nom du conteneur de staging."
  type        = string
  default     = "cod-metrics-staging"
}

variable "network_name" {
  description = "Nom du reseau Docker partage par les conteneurs CI/CD."
  type        = string
  default     = "cicd-network"
}

variable "app_port" {
  description = "Port hote expose pour atteindre l'application de staging."
  type        = number
  default     = 8001
}
