# GreenLightPA - Realtime Prior Authorization Navigator

Automate the prior‑authorization (PA) process in real time—from clinical note to payer approval—reducing clerical load, turnaround time, and denial rates for high‑volume specialty clinics (oncology, rheumatology, imaging).

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

### 1. Launch Infrastructure

```bash
# Clone the repository
git clone <repository-url>
cd GreenLightPA

# Start the containerized services
docker compose up -d

# Verify services are running
docker compose ps
```

This starts:
- **PostgreSQL 16** with pgvector extension on port 5432
- **FastAPI application** on port 8000
- **pgAdmin** web interface on port 5050
- **Redis** cache on port 6379

### 2. Generate Synthetic Data

```bash
# Generate 500 synthetic patients with oncology/rheumatology conditions
python scripts/generate_synthea_data.py -p 500 -s oncology rheumatology

# Or use the API endpoint
curl -X POST "http://localhost:8000/api/v1/synthetic/generate" \
  -H "Content-Type: application/json" \
  -d '{"num_patients": 500, "specialties": ["oncology", "rheumatology"]}'
```

### 3. Process and Embed Data

The pipeline automatically:
1. **Extracts** clinical notes from FHIR bundles
2. **De-identifies** PHI using Philter-py (HIPAA Safe Harbor)
3. **Generates** vector embeddings using sentence-transformers
4. **Stores** everything in PostgreSQL with pgvector

Monitor progress:
```bash
curl "http://localhost:8000/api/v1/synthetic/status"
```

### 4. Test Vector Similarity Search

```bash
# Run comprehensive retrieval tests
python scripts/test_retrieval.py --performance

# Test via API
curl "http://localhost:8000/api/v1/synthetic/search-policies?query_text=chemotherapy%20prior%20authorization&specialty=oncology"
```

## 📊 Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Synthea       │ -> │   FHIR Bundles  │ -> │   Clinical      │
│   Generator     │    │   (Raw Data)    │    │   Notes Extract │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │ <- │   Embeddings    │ <- │   PHI De-ID     │
│   + pgvector    │    │   (384-dim)     │    │   (Philter)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI + Python 3.11 | Async API with type safety |
| **Database** | PostgreSQL 16 + pgvector | Vector similarity search |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | 384-dim vectors, CPU-optimized |
| **PHI De-ID** | Philter-py | HIPAA Safe Harbor compliance |
| **Synthetic Data** | Synthea | Realistic FHIR patient data |
| **Infrastructure** | Docker Compose | Containerized development |

## 📁 Project Structure

```
GreenLightPA/
├── app/
│   ├── api/v1/endpoints/          # FastAPI route handlers
│   ├── core/                      # Configuration, database
│   ├── models/                    # SQLAlchemy ORM models
│   ├── schemas/                   # Pydantic request/response models
│   └── services/                  # Business logic services
│       ├── embedding_service.py   # Vector embeddings
│       ├── fhir_processor.py      # FHIR bundle processing
│       ├── phi_deidentifier.py    # PHI de-identification
│       └── synthetic_pipeline.py  # Pipeline orchestration
├── scripts/
│   ├── generate_synthea_data.py   # Standalone Synthea runner
│   ├── test_retrieval.py          # Vector search testing
│   └── init.sql                   # Database initialization
├── synthea_modules/
│   └── PriorAuth.json             # Custom Synthea module
├── docker-compose.yml             # Infrastructure definition
├── Dockerfile                     # Application container
└── requirements.txt               # Python dependencies
```

## 🔧 Development Commands

### Database Management

```bash
# Access PostgreSQL directly
docker exec -it greenlightpa-postgres-1 psql -U postgres -d greenlight

# Access pgAdmin web interface
open http://localhost:5050
# Email: admin@greenlightpa.com, Password: admin
```

### API Development

```bash
# View API documentation
open http://localhost:8000/docs

# Health check
curl http://localhost:8000/health

# List generated patients
curl "http://localhost:8000/api/v1/synthetic/patients?limit=5"

# List clinical notes
curl "http://localhost:8000/api/v1/synthetic/notes?specialty=oncology&prior_auth_only=true"
```

### Data Pipeline Operations

```bash
# Generate synthetic data
python scripts/generate_synthea_data.py -p 100 -s oncology

# Validate Synthea output
python scripts/generate_synthea_data.py --validate-only

# Test embeddings and similarity search
python scripts/test_retrieval.py --verbose

# Performance test
python scripts/test_retrieval.py --performance
```

## 📈 Key Performance Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **Data Generation** | 500 patients in ~5 min | Synthea + processing pipeline |
| **Embedding Speed** | <1s per note | sentence-transformers on CPU |
| **Search Latency** | <100ms | pgvector similarity queries |
| **Storage Efficiency** | ~2MB per 100 patients | Compressed FHIR + embeddings |

## 🔍 Sample Queries

### Policy Similarity Search
```sql
SELECT * FROM search_similar_policies(
    '[0.1, 0.2, ...]'::vector,  -- Query embedding
    0.8,                        -- Similarity threshold
    5,                          -- Max results
    'oncology'                  -- Specialty filter
);
```

### Clinical Notes by Similarity
```sql
SELECT note_id, specialty, prior_auth_status,
       1 - (embedding <=> '[0.1, 0.2, ...]'::vector) as similarity
FROM clinical_notes 
WHERE embedding IS NOT NULL
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

## 🧪 Testing & Validation

### End-to-End Pipeline Test
```bash
# 1. Clean start
docker compose down -v
docker compose up -d

# 2. Generate small dataset
python scripts/generate_synthea_data.py -p 50

# 3. Run full pipeline via API
curl -X POST "http://localhost:8000/api/v1/synthetic/generate" \
  -H "Content-Type: application/json" \
  -d '{"num_patients": 50, "specialties": ["oncology"]}'

# 4. Wait for completion and test retrieval
python scripts/test_retrieval.py
```

### Data Quality Checks
```bash
# Check synthetic data quality
docker exec -it greenlightpa-postgres-1 psql -U postgres -d greenlight -c "
SELECT 
  COUNT(*) as total_patients,
  COUNT(DISTINCT patient_id) as unique_patients,
  (SELECT COUNT(*) FROM clinical_notes) as total_notes,
  (SELECT COUNT(*) FROM clinical_notes WHERE prior_auth_required = true) as pa_required_notes
FROM synthetic_patients;
"
```

## 🔒 Security & Compliance

- **PHI De-identification**: Philter-py for HIPAA Safe Harbor compliance
- **Synthetic Data**: No real patient information used
- **Database Encryption**: TLS 1.3 for connections
- **Access Control**: Container network isolation
- **Audit Logging**: All pipeline operations logged

## 📚 API Documentation

Full interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/synthetic/generate` | POST | Start synthetic data generation |
| `/api/v1/synthetic/status` | GET | Pipeline status and metrics |
| `/api/v1/synthetic/patients` | GET | List synthetic patients |
| `/api/v1/synthetic/notes` | GET | List clinical notes (filterable) |
| `/api/v1/synthetic/search-policies` | GET | Vector similarity search |

## ⚡ Next Steps

1. **Scale Testing**: Generate 10k+ patients for performance validation
2. **Fine-tuning**: Train custom embeddings on medical text
3. **RAG Integration**: Connect to LLM for policy reasoning
4. **Real Data**: Integrate with EHR systems via SMART-on-FHIR
5. **Production**: Add authentication, monitoring, and deployment automation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
