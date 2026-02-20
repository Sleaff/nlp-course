# Text to Persons - NER API

Kenneth Plum Toft - s195171

## Running with/without docker

**Important:** You need to set your CampusAI API key as an environment variable, if you wish to run the endpoint /v1/extract-persons.

### Build the Docker image:
```bash
docker build -t text-to-persons .
```

### Run the Docker image:
```bash
docker run -p 8000:8000 -e CAMPUSAI_API_KEY="your_api_key_here" text-to-persons
```

### Run application locally
To run the applcation locally you need to create a .env file in root, filling it out with the following content.
```bash
CAMPUSAI_API_KEY=your_api_key_here
```

### Swagger
Swagger UI: http://localhost:8000/docs