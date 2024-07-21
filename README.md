
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql) ![MinIO](https://img.shields.io/badge/MinIO-F68D20?style=for-the-badge&logo=minio) ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

# Meme store 🗑	

Meme-store is a Python web application using FastAPI that provides a RESTful API for managing a collection of memes. The application is divided into two main services: a service with a public API responsible for business logic, and a service for working with media files, using S3-compatible MinIO storage and PostgreSQL relational database.

## Run Locally

Clone the project

```bash
  git clone https://github.com/NikitaPisarev/meme-store.git
```

Go to the project directory

```bash
  cd meme-store
```

Run docker compose

```bash
  docker compose up -d --build
```



## License

[Apache-2.0](https://choosealicense.com/licenses/apache-2.0/)

