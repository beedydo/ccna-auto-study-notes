# Terraform: declarative HCL. Order of blocks doesn't matter; Terraform builds a graph.
# terraform init -> terraform plan -> terraform apply  (state kept in terraform.tfstate)
terraform {
  required_providers {
    iosxe = {
      source = "CiscoDevNet/iosxe"
    }
  }
}

provider "iosxe" {
  host     = "10.10.20.11"   # NETCONF over SSH, port 830 by default
  username = "admin"
  password = var.iosxe_password
}

variable "iosxe_password" {
  type      = string
  sensitive = true
}

resource "iosxe_system" "sw1" {
  hostname = "branch1-sw1"
}

resource "iosxe_vlan" "users" {
  vlan_id = 10
  name    = "USERS"
}

resource "iosxe_vlan" "voice" {
  vlan_id = 20
  name    = "VOICE"
}
