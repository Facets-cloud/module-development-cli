# Module with provider block - should fail validation
provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "test" {
  ami           = "ami-12345"
  instance_type = "t2.micro"
  
  tags = {
    Name = "test-instance"
  }
}
