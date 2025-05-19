# Attribute Finder

A machine learning service for extracting fashion attributes using LLMs and high quality product images.

## 🚀 Features

- Automated attribute extraction from product descriptions and images
- Color analysis from product images
- Multi-language support

## 📋 Prerequisites

- Python 3.11+
- Docker
- OpenAI API key
- Make
- uv

## 🛠 Installation

1. Clone repository:
(requires SSH Key + connected to company network)
```bash
git clone git@gitlab.hachmeister-partner.de:mfriebe/attribut-finder-api.git
cd attribut-finder-api
```

## 🚦 Usage

### Docker (Recommended)

```bash
make run-with-docker
```

### Local Development

```bash
make run-response-model-dev
```

## 📁 Project Structure

```
attribute_finder/
├── src/ # Source code
│ ├── response/ # Response generation service
│ └── data_ingest/ # Data ingestion service
├── services/ # Service configurations
├── data/ # Data storage
```
