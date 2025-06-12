variable "instance" {
  description = "Instance configuration"
  type = object({
    kind    = string
    flavor  = string
    version = string
  })
}

variable "instance_name" {
  description = "Instance name"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "inputs" {
  description = "Inputs"
  type        = object({})
}
