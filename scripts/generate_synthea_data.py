#!/usr/bin/env python3
"""
Standalone script for generating synthetic patient data using Synthea
Can be run independently or as part of the pipeline
"""

import argparse
import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_synthea_data(
    num_patients: int = 500,
    specialties: list = None,
    output_dir: str = "./data/fhir",
    modules_dir: str = "./synthea_modules"
):
    """
    Generate synthetic patient data using Synthea Docker container
    
    Args:
        num_patients: Number of patients to generate
        specialties: List of specialty modules to include
        output_dir: Directory for FHIR output
        modules_dir: Directory containing custom Synthea modules
    """
    if specialties is None:
        specialties = ["oncology", "rheumatology"]
    
    # Ensure directories exist
    output_path = Path(output_dir)
    modules_path = Path(modules_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not modules_path.exists():
        logger.error(f"Modules directory not found: {modules_path}")
        return False
    
    # Build specialty modules string
    specialty_modules = ",".join(specialties)
    
    # Prepare Synthea command
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{output_path.absolute()}:/synthea/output",
        "-v", f"{modules_path.absolute()}:/synthea/src/main/resources/modules",
        "synthetichealth/synthea:latest",
        "-p", str(num_patients),
        "-m", f"{specialty_modules},PriorAuth",
        "--exporter.fhir.export", "true",
        "--exporter.hospital.fhir.export", "false",
        "--exporter.practitioner.fhir.export", "false"
    ]
    
    logger.info(f"Running Synthea command: {' '.join(cmd)}")
    logger.info(f"Generating {num_patients} patients with specialties: {specialties}")
    logger.info(f"Output directory: {output_path.absolute()}")
    
    try:
        # Run Synthea
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if process.returncode != 0:
            logger.error(f"Synthea failed with return code {process.returncode}")
            logger.error(f"stderr: {process.stderr}")
            return False
        
        logger.info("Synthea generation completed successfully")
        logger.info(f"stdout: {process.stdout[:500]}...")
        
        # Verify output files
        fhir_files = list(output_path.glob("*.json"))
        logger.info(f"Generated {len(fhir_files)} FHIR bundle files")
        
        if len(fhir_files) == 0:
            logger.error("No FHIR files generated")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Synthea generation timed out after 1 hour")
        return False
    except Exception as e:
        logger.error(f"Error running Synthea: {e}")
        return False


def validate_synthea_output(output_dir: str = "./data/fhir"):
    """
    Validate the generated Synthea output
    
    Args:
        output_dir: Directory containing FHIR files
    """
    output_path = Path(output_dir)
    
    if not output_path.exists():
        logger.error(f"Output directory does not exist: {output_path}")
        return False
    
    fhir_files = list(output_path.glob("*.json"))
    logger.info(f"Found {len(fhir_files)} FHIR files")
    
    if len(fhir_files) == 0:
        logger.error("No FHIR files found")
        return False
    
    # Validate a sample of files
    sample_size = min(5, len(fhir_files))
    valid_files = 0
    
    for i, fhir_file in enumerate(fhir_files[:sample_size]):
        try:
            with open(fhir_file, 'r') as f:
                bundle = json.load(f)
            
            # Basic validation
            if bundle.get('resourceType') != 'Bundle':
                logger.warning(f"File {fhir_file} is not a FHIR Bundle")
                continue
            
            entries = bundle.get('entry', [])
            if len(entries) == 0:
                logger.warning(f"File {fhir_file} has no entries")
                continue
            
            # Check for Patient resource
            has_patient = any(
                entry.get('resource', {}).get('resourceType') == 'Patient'
                for entry in entries
            )
            
            if not has_patient:
                logger.warning(f"File {fhir_file} has no Patient resource")
                continue
            
            valid_files += 1
            logger.info(f"✓ Validated {fhir_file} ({len(entries)} entries)")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {fhir_file}: {e}")
        except Exception as e:
            logger.error(f"Error validating {fhir_file}: {e}")
    
    logger.info(f"Validated {valid_files}/{sample_size} sample files")
    return valid_files > 0


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description="Generate synthetic patient data using Synthea"
    )
    parser.add_argument(
        "-p", "--patients",
        type=int,
        default=500,
        help="Number of patients to generate (default: 500)"
    )
    parser.add_argument(
        "-s", "--specialties",
        nargs="+",
        default=["oncology", "rheumatology"],
        help="Medical specialties to focus on (default: oncology rheumatology)"
    )
    parser.add_argument(
        "-o", "--output",
        default="./data/fhir",
        help="Output directory for FHIR files (default: ./data/fhir)"
    )
    parser.add_argument(
        "-m", "--modules",
        default="./synthea_modules",
        help="Directory containing custom Synthea modules (default: ./synthea_modules)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing output, don't generate new data"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.validate_only:
        logger.info("Validating existing Synthea output...")
        success = validate_synthea_output(args.output)
    else:
        logger.info("Starting Synthea data generation...")
        success = generate_synthea_data(
            num_patients=args.patients,
            specialties=args.specialties,
            output_dir=args.output,
            modules_dir=args.modules
        )
        
        if success:
            logger.info("Validating generated output...")
            validate_synthea_output(args.output)
    
    if success:
        logger.info("✓ Synthea data generation completed successfully")
        sys.exit(0)
    else:
        logger.error("✗ Synthea data generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main() 