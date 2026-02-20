# Intro
The Endpoints use various methods to extract the text from the PDF to a markdown format. Next i use SpaCy (en_core_web_sm) to post-process the text into good machine readable text


# There exists 3 endpoints

/v1/extract-sentences               # fastest results
/v1/extract-sentences-marker        # Best results but slow (can use GPU to speed up)
/v1/extract-sentences-docling       # Alternative results


### Build the Docker image:
```bash
docker build -t pdf-to-sentences .
```

### Run the Docker image:
```bash
docker run -p 8000:8000 pdf-to-sentences