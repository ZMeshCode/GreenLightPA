#!/usr/bin/env python3
"""
Standalone script for testing vector similarity retrieval
Proves that pgvector search works with the synthetic data
"""

import argparse
import asyncio
import asyncpg
import json
import logging
import sys
from pathlib import Path
import os

# Add the app directory to Python path so we can import our services
sys.path.append(str(Path(__file__).parent.parent))

from app.services.embedding_service import EmbeddingService
from app.core.config import get_settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_database_connection(db_url: str):
    """Test basic database connectivity"""
    try:
        conn = await asyncpg.connect(db_url)
        
        # Test basic query
        result = await conn.fetchval("SELECT 1")
        assert result == 1
        
        # Test pgvector extension
        result = await conn.fetchval("SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'")
        if result == 0:
            logger.error("pgvector extension not installed")
            await conn.close()
            return False
        
        logger.info("✓ Database connection successful")
        logger.info("✓ pgvector extension is installed")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def test_embedding_service():
    """Test the embedding service"""
    try:
        embedding_service = EmbeddingService()
        
        if not embedding_service.is_ready:
            logger.error("Embedding service is not ready")
            return False, None
        
        # Test basic embedding
        test_text = "Patient presents with advanced oncology condition requiring prior authorization"
        embedding = embedding_service.embed_text(test_text)
        
        if not embedding or len(embedding) == 0:
            logger.error("Failed to generate embedding")
            return False, None
        
        logger.info(f"✓ Embedding service working (dimension: {len(embedding)})")
        return True, embedding_service
        
    except Exception as e:
        logger.error(f"Embedding service test failed: {e}")
        return False, None


async def test_policy_search(db_url: str, embedding_service: EmbeddingService):
    """Test policy chunk similarity search"""
    try:
        conn = await asyncpg.connect(db_url)
        
        # Check if we have policy chunks
        chunk_count = await conn.fetchval("SELECT COUNT(*) FROM policy_chunks")
        logger.info(f"Found {chunk_count} policy chunks in database")
        
        if chunk_count == 0:
            logger.warning("No policy chunks found. Skipping policy search test.")
            await conn.close()
            return True
        
        # Generate embedding for test query
        test_query = "chemotherapy prior authorization requirements"
        query_embedding = embedding_service.embed_text(test_query)
        
        # Convert to PostgreSQL array format
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Test the search function
        query = """
            SELECT * FROM search_similar_policies(
                $1::vector,
                0.1,  -- Low threshold to get results
                5,
                NULL
            )
        """
        
        results = await conn.fetch(query, embedding_str)
        
        logger.info(f"✓ Policy search returned {len(results)} results")
        
        for i, result in enumerate(results[:3]):  # Show top 3
            logger.info(f"  {i+1}. {result['payer_id']} - {result['policy_id']} "
                       f"(similarity: {result['similarity']:.3f})")
            logger.info(f"     {result['chunk_text'][:100]}...")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Policy search test failed: {e}")
        return False


async def test_clinical_notes_search(db_url: str, embedding_service: EmbeddingService):
    """Test clinical notes similarity search"""
    try:
        conn = await asyncpg.connect(db_url)
        
        # Check if we have clinical notes
        notes_count = await conn.fetchval("SELECT COUNT(*) FROM clinical_notes")
        logger.info(f"Found {notes_count} clinical notes in database")
        
        if notes_count == 0:
            logger.warning("No clinical notes found. Skipping notes search test.")
            await conn.close()
            return True
        
        # Get a sample note to test similarity
        sample_note = await conn.fetchrow("""
            SELECT note_id, LEFT(deidentified_text, 200) as text_preview, specialty
            FROM clinical_notes 
            WHERE deidentified_text IS NOT NULL 
            LIMIT 1
        """)
        
        if not sample_note:
            logger.warning("No processed notes found. Skipping notes search test.")
            await conn.close()
            return True
        
        logger.info(f"Using sample note from {sample_note['specialty']} specialty")
        logger.info(f"Sample text: {sample_note['text_preview']}...")
        
        # Generate embedding for similar query
        query_text = f"patient with {sample_note['specialty']} condition"
        query_embedding = embedding_service.embed_text(query_text)
        
        # Convert to PostgreSQL array format
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Test similarity search
        query = """
            SELECT note_id, patient_id, specialty, prior_auth_status,
                   LEFT(deidentified_text, 100) as text_preview,
                   1 - (embedding <=> $1::vector) as similarity
            FROM clinical_notes 
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT 5
        """
        
        results = await conn.fetch(query, embedding_str)
        
        logger.info(f"✓ Clinical notes search returned {len(results)} results")
        
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result['note_id']} ({result['specialty']}) "
                       f"- {result['prior_auth_status']} "
                       f"(similarity: {result['similarity']:.3f})")
            logger.info(f"     {result['text_preview']}...")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Clinical notes search test failed: {e}")
        return False


async def run_performance_test(db_url: str, embedding_service: EmbeddingService):
    """Run a performance test on vector search"""
    try:
        conn = await asyncpg.connect(db_url)
        
        # Check total records
        total_notes = await conn.fetchval("SELECT COUNT(*) FROM clinical_notes WHERE embedding IS NOT NULL")
        total_policies = await conn.fetchval("SELECT COUNT(*) FROM policy_chunks WHERE chunk_embedding IS NOT NULL")
        
        logger.info(f"Performance test with {total_notes} notes and {total_policies} policies")
        
        if total_notes == 0 and total_policies == 0:
            logger.warning("No embedded data found for performance test")
            await conn.close()
            return True
        
        # Test query
        test_queries = [
            "oncology chemotherapy treatment",
            "rheumatoid arthritis biologic therapy",
            "imaging MRI scan prior authorization",
            "patient diagnosis and treatment plan"
        ]
        
        import time
        
        for query_text in test_queries:
            start_time = time.time()
            
            # Generate embedding
            query_embedding = embedding_service.embed_text(query_text)
            embedding_time = time.time() - start_time
            
            # Search clinical notes
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            search_start = time.time()
            results = await conn.fetch("""
                SELECT note_id, 1 - (embedding <=> $1::vector) as similarity
                FROM clinical_notes 
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> $1::vector
                LIMIT 10
            """, embedding_str)
            search_time = time.time() - search_start
            
            total_time = time.time() - start_time
            
            logger.info(f"Query: '{query_text}'")
            logger.info(f"  Embedding: {embedding_time:.3f}s, Search: {search_time:.3f}s, Total: {total_time:.3f}s")
            logger.info(f"  Found {len(results)} results, top similarity: {results[0]['similarity']:.3f}")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        return False


async def main_async(args):
    """Main async function"""
    settings = get_settings()
    db_url = settings.database_url.replace("postgresql://", "postgresql://")
    
    logger.info("=== Vector Similarity Retrieval Test ===")
    
    # Test 1: Database connection
    logger.info("1. Testing database connection...")
    if not await test_database_connection(db_url):
        logger.error("Database connection test failed")
        return False
    
    # Test 2: Embedding service
    logger.info("2. Testing embedding service...")
    embedding_ready, embedding_service = await test_embedding_service()
    if not embedding_ready:
        logger.error("Embedding service test failed")
        return False
    
    # Test 3: Policy search
    logger.info("3. Testing policy chunk similarity search...")
    if not await test_policy_search(db_url, embedding_service):
        logger.error("Policy search test failed")
        return False
    
    # Test 4: Clinical notes search
    logger.info("4. Testing clinical notes similarity search...")
    if not await test_clinical_notes_search(db_url, embedding_service):
        logger.error("Clinical notes search test failed")
        return False
    
    # Test 5: Performance test
    if args.performance:
        logger.info("5. Running performance test...")
        if not await run_performance_test(db_url, embedding_service):
            logger.error("Performance test failed")
            return False
    
    logger.info("=== All tests passed! ===")
    logger.info("✓ pgvector similarity search is working correctly")
    return True


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description="Test vector similarity retrieval with pgvector"
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        success = asyncio.run(main_async(args))
        if success:
            logger.info("✓ Vector retrieval test completed successfully")
            sys.exit(0)
        else:
            logger.error("✗ Vector retrieval test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 