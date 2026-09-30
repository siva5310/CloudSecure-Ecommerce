resource "aws_instance" "cloudsecure" {
  ami                         = "ami-0199ac7c9fbf9ed83"
  instance_type               = "t3.micro"
  subnet_id                   = "subnet-0947c3ed38a2f2ea9"
  vpc_security_group_ids     = ["sg-05071713fb9848fd6"]
  key_name                    = "cloudsecure-key"
  iam_instance_profile       = "CloudSecure-Ecommerce-S3-Role"
  associate_public_ip_address = true

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = "CloudSecure-Ecommerce"
  }
}
