# Additional file with provider block
provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "test" {
  name     = "test-rg"
  location = "West US"
}
