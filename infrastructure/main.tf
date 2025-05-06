provider "aws" {
  region = "eu-central-1"  # или ваш регион
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "online-cinema-vpc"
  }
}

# Публичные подсети
resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "online-cinema-public-${count.index + 1}"
  }
}

# Приватные подсети
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "online-cinema-private-${count.index + 1}"
  }
}

# RDS
resource "aws_db_instance" "postgres" {
  identifier        = "online-cinema-db"
  engine           = "postgres"
  engine_version   = "15.12"
  instance_class   = "db.t3.micro"
  allocated_storage = 20

  db_name  = "cinema_db"
  username = "postgres"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.rds.name

  skip_final_snapshot = true
}

# ElastiCache
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "online-cinema-redis"
  engine              = "redis"
  node_type           = "cache.t3.micro"
  num_cache_nodes     = 1
  parameter_group_name = "default.redis7"
  port                = 6379
  security_group_ids  = [aws_security_group.redis.id]
  subnet_group_name   = aws_elasticache_subnet_group.redis.name
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "online-cinema-cluster"
}

# ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = "online-cinema"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512

  container_definitions = jsonencode([
    {
      name  = "nginx"
      image = "${var.ecr_repository_url}/nginx:latest"
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        }
      ]
      links = ["web"]
    },
    {
      name  = "web"
      image = "${var.ecr_repository_url}:latest"
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "DATABASE_URL"
          value = "postgresql+asyncpg://${aws_db_instance.postgres.username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
        },
        {
          name  = "REDIS_HOST"
          value = aws_elasticache_cluster.redis.cache_nodes[0].address
        }
      ]
    }
  ])
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "online-cinema-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id
}

# ECS Service
resource "aws_ecs_service" "app" {
  name            = "online-cinema"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "web"
    container_port   = 8000
  }
}

# Variables
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "ecr_repository_url" {
  description = "ECR repository URL"
  type        = string
} 