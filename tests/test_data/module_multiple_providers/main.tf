# Module with multiple providers - should fail validation
provider "aws" {
  region = "us-west-2"
  alias  = "west"
}

provider "aws" {
  region = "us-east-1"
  alias  = "east"
}

resource "aws_instance" "west_instance" {
  provider      = aws.west
  ami           = "ami-12345"
  instance_type = "t2.micro"
}
