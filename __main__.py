import pulumi
import pulumi_aws as aws

# VPC
vpc = aws.ec2.Vpc("poridhi-vpc",
                  cidr_block="10.0.0.0/16",
                  instance_tenancy="default",
                  tags={
                      "Name": "poridhi-vpc",
                  })
# Public Subnet
public_subnet = aws.ec2.Subnet("poridhi-public-subnet",
                               vpc_id=vpc.id,
                               cidr_block="10.0.1.0/24",
                               availability_zone="ap-southeast-1a",
                               tags={
                                   "Name": "poridhi-public-subnet",
                               })

# Private Subnet
private_subnet = aws.ec2.Subnet("poridhi-private-subnet",
                                vpc_id=vpc.id,
                                cidr_block="10.0.2.0/24",
                                availability_zone="ap-southeast-1c",
                                tags={
                                    "Name": "poridhi-private-subnet",
                                })

# Internet Gateway
igw = aws.ec2.InternetGateway("poridhi-igw",
                              vpc_id=vpc.id,
                              tags={
                                  "Name": "poridhi-igw",
                              })

# Elastic IP for the Nat Gateway
nat_eip = aws.ec2.Eip("poridhi-nat-eip",
                      domain="vpc",
                      tags={
                          "Name": "poridhi-nat-eip",
                      })

# NAT Gateway
nat_gateway = aws.ec2.NatGateway("poridhi-nat-gateway",
                                 subnet_id=public_subnet.id,
                                 connectivity_type="public",
                                 allocation_id=nat_eip.id,
                                 tags={
                                     "Name": "poridhi-nat-gateway",
                                 },
                                 opts=pulumi.ResourceOptions(
                                     depends_on=[igw, nat_eip])
                                 )

# Public Route Table
public_route_table = aws.ec2.RouteTable("poridhi-public-route-table",
                                        vpc_id=vpc.id,
                                        routes=[
                                            aws.ec2.RouteTableRouteArgs(cidr_block="0.0.0.0/0",
                                                                        gateway_id=igw.id),
                                        ],
                                        tags={
                                            "Name": "poridhi-public-route-table",
                                        })

# Public Route Table Association
public_route_table_association = aws.ec2.RouteTableAssociation("poridhi-public-rta",
                                                               subnet_id=public_subnet.id,
                                                               route_table_id=public_route_table.id
                                                               )

# Private Route Table
private_route_table = aws.ec2.RouteTable("poridhi-private-route-table",
                                         vpc_id=vpc.id,
                                         routes=[
                                             aws.ec2.RouteTableRouteArgs(cidr_block="0.0.0.0/0",
                                                                         nat_gateway_id=nat_gateway.id),
                                         ],
                                         tags={
                                             "Name": "poridhi-private-route-table",
                                         })

# Private Route Table Association
private_route_table_association = aws.ec2.RouteTableAssociation("poridhi-private-rta",
                                                                subnet_id=private_subnet.id,
                                                                route_table_id=private_route_table.id
                                                                )

# Public Security Group
public_security_group = aws.ec2.SecurityGroup("poridhi-public-sg",
                                              description="Allow inbound SSH from my IP and all outbound",
                                              vpc_id=vpc.id,
                                              ingress=[{
                                                  "from_port": 22,
                                                  "protocol": "tcp",
                                                  "to_port": 22,
                                                  "cidr_blocks": ["103.191.50.14/32"],
                                              }],
                                              egress=[{
                                                  "from_port": 0,
                                                  "protocol": -1,
                                                  "to_port": 0,
                                                  "cidr_blocks": ["0.0.0.0/0"],
                                              }],
                                              tags={
                                                  "Name": "poridhi-public-sg",
                                              })

# Private Security Group
private_security_group = aws.ec2.SecurityGroup("poridhi-private-sg",
                                               description="Allow inbound SSH from public_security_group and all outbound",
                                               vpc_id=vpc.id,
                                               ingress=[{
                                                   "from_port": 22,
                                                   "protocol": "tcp",
                                                   "to_port": 22,
                                                   "security_groups": [public_security_group.id],
                                               }],
                                               egress=[{
                                                   "from_port": 0,
                                                   "protocol": -1,
                                                   "to_port": 0,
                                                   "cidr_blocks": ["0.0.0.0/0"],
                                               }],
                                               tags={
                                                   "Name": "poridhi-private-sg",
                                               })

# Look up for latest Ubuntu Ami
ubuntu_ami = aws.ec2.get_ami(
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="virtualization-type",
            values=["hvm"],
        ),
    ],
    most_recent=True,
    owners=["099720109477"])

# Public EC2
public_ec2 = aws.ec2.Instance("poridhi-public-ec2",
                              ami=ubuntu_ami.id,
                              instance_type="t2.micro",
                              subnet_id=public_subnet.id,
                              associate_public_ip_address=True,
                              key_name="poridhi-key",
                              vpc_security_group_ids=[
                                  public_security_group.id],
                              tags={
                                  "Name": "poridhi-public-ec2",
                              })

# Private EC2
private_ec2 = aws.ec2.Instance("poridhi-private-ec2",
                               ami=ubuntu_ami.id,
                               instance_type="t2.micro",
                               subnet_id=private_subnet.id,
                               associate_public_ip_address=False,
                               key_name="poridhi-key",
                               vpc_security_group_ids=[
                                   private_security_group.id],
                               tags={
                                   "Name": "poridhi-private-ec2",
                               })

pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_id", public_subnet.id)
pulumi.export("igw_id", igw.id)
pulumi.export("nat_eip_public_ip", nat_eip.public_ip)
pulumi.export("nat_gateway_id", nat_gateway.id)
pulumi.export("public_route_table_id", public_route_table.id)
pulumi.export("private_route_table_id", private_route_table.id)
pulumi.export("ubuntu_ami_id", ubuntu_ami.id)
pulumi.export("public_instance_id", public_ec2.id)
pulumi.export("public_instance_ip", public_ec2.public_ip)
pulumi.export("private_instance_id", private_ec2.id)
pulumi.export("private_instance_ip", private_ec2.private_ip)

