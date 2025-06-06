"""
PHI De-identification Service
Uses Philter-py for HIPAA Safe Harbor compliant de-identification
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional
import hashlib

try:
    from philter import Philter
    PHILTER_AVAILABLE = True
except ImportError:
    PHILTER_AVAILABLE = False
    logging.warning("Philter-py not available. Using basic regex-based de-identification.")

logger = logging.getLogger(__name__)


class PHIDeidentifier:
    """Service for de-identifying PHI in clinical text"""
    
    def __init__(self):
        self.philter_client = None
        self.fallback_patterns = self._create_fallback_patterns()
        
        if PHILTER_AVAILABLE:
            try:
                self.philter_client = Philter()
                logger.info("Philter-py initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Philter: {e}. Using fallback patterns.")
                self.philter_client = None
        else:
            logger.warning("Using fallback regex patterns for PHI de-identification")
    
    async def deidentify_text(self, text: str) -> str:
        """
        De-identify PHI in clinical text
        
        Args:
            text: Original clinical text containing PHI
            
        Returns:
            De-identified text with PHI replaced
        """
        if not text or not text.strip():
            return text
        
        try:
            if self.philter_client:
                return await self._deidentify_with_philter(text)
            else:
                return self._deidentify_with_fallback(text)
        except Exception as e:
            logger.error(f"De-identification failed: {e}")
            # Return fallback even if Philter fails
            return self._deidentify_with_fallback(text)
    
    async def _deidentify_with_philter(self, text: str) -> str:
        """De-identify using Philter-py"""
        try:
            # Run Philter in thread pool since it may be CPU-intensive
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self.philter_client.apply, 
                text
            )
            
            return result.filtered_text if hasattr(result, 'filtered_text') else str(result)
            
        except Exception as e:
            logger.error(f"Philter processing failed: {e}")
            raise
    
    def _deidentify_with_fallback(self, text: str) -> str:
        """De-identify using regex patterns (fallback method)"""
        deidentified_text = text
        
        try:
            # Apply each pattern
            for pattern_name, pattern_info in self.fallback_patterns.items():
                pattern = pattern_info['pattern']
                replacement = pattern_info['replacement']
                
                deidentified_text = re.sub(
                    pattern, 
                    replacement, 
                    deidentified_text, 
                    flags=re.IGNORECASE | re.MULTILINE
                )
            
            logger.debug(f"Applied {len(self.fallback_patterns)} de-identification patterns")
            return deidentified_text
            
        except Exception as e:
            logger.error(f"Fallback de-identification failed: {e}")
            return "[DE-IDENTIFICATION FAILED]"
    
    def _create_fallback_patterns(self) -> Dict[str, Dict[str, str]]:
        """Create regex patterns for basic PHI de-identification"""
        return {
            # Names (basic patterns)
            'names': {
                'pattern': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
                'replacement': '[NAME]'
            },
            
            # Social Security Numbers
            'ssn': {
                'pattern': r'\b\d{3}-?\d{2}-?\d{4}\b',
                'replacement': '[SSN]'
            },
            
            # Phone Numbers
            'phone': {
                'pattern': r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
                'replacement': '[PHONE]'
            },
            
            # Email Addresses
            'email': {
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'replacement': '[EMAIL]'
            },
            
            # Medical Record Numbers (MRN)
            'mrn': {
                'pattern': r'\b(?:MRN|Medical Record|Patient ID):?\s*([A-Z0-9]{6,})\b',
                'replacement': r'MRN: [MRN]'
            },
            
            # Dates (MM/DD/YYYY, MM-DD-YYYY, Month DD, YYYY)
            'dates': {
                'pattern': r'\b(?:\d{1,2}[/\-]\d{1,2}[/\-]\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b',
                'replacement': '[DATE]'
            },
            
            # Ages over 89
            'ages_over_89': {
                'pattern': r'\b(?:age\s+)?(?:9[0-9]|[1-9]\d{2,})\s*(?:years?\s*old|y\.?o\.?)\b',
                'replacement': '[AGE>89]'
            },
            
            # ZIP codes (5 digit codes, keeping only first 3 if needed)
            'zip_specific': {
                'pattern': r'\b\d{5}(?:-\d{4})?\b',
                'replacement': '[ZIP]'
            },
            
            # Vehicle identifiers
            'vehicle_ids': {
                'pattern': r'\b[A-Z0-9]{17}\b',  # VIN numbers
                'replacement': '[VIN]'
            },
            
            # Account numbers
            'account_numbers': {
                'pattern': r'\b(?:Account|Acct)\.?\s*#?\s*([A-Z0-9]{8,})\b',
                'replacement': r'Account: [ACCOUNT]'
            },
            
            # URLs
            'urls': {
                'pattern': r'https?://[^\s]+',
                'replacement': '[URL]'
            },
            
            # IP Addresses
            'ip_addresses': {
                'pattern': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                'replacement': '[IP]'
            }
        }
    
    def generate_synthetic_replacement(self, phi_type: str, original_value: str) -> str:
        """
        Generate consistent synthetic replacements for PHI
        This ensures the same PHI value gets the same replacement across all notes
        """
        # Create a hash of the original value for consistency
        hash_input = f"{phi_type}_{original_value}".encode()
        hash_value = hashlib.md5(hash_input).hexdigest()[:8].upper()
        
        replacements = {
            'NAME': f"Patient_{hash_value}",
            'SSN': f"XXX-XX-{hash_value[:4]}",
            'PHONE': f"({hash_value[:3]}) {hash_value[3:6]}-{hash_value[6:]}",
            'EMAIL': f"patient_{hash_value}@example.com",
            'MRN': f"MRN_{hash_value}",
            'DATE': f"[DATE_{hash_value[:4]}]",
            'ZIP': f"{hash_value[:5]}",
            'ACCOUNT': f"ACCT_{hash_value}"
        }
        
        return replacements.get(phi_type, f"[{phi_type}_{hash_value}]")
    
    def validate_deidentification(self, original_text: str, deidentified_text: str) -> Dict[str, Any]:
        """
        Validate the de-identification process
        
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'is_valid': True,
            'issues': [],
            'phi_detected': [],
            'reduction_ratio': 0.0
        }
        
        try:
            # Check for potential remaining PHI using patterns
            for pattern_name, pattern_info in self.fallback_patterns.items():
                matches = re.findall(pattern_info['pattern'], deidentified_text, re.IGNORECASE)
                if matches:
                    validation_result['is_valid'] = False
                    validation_result['issues'].append(f"Potential {pattern_name} found: {len(matches)} instances")
                    validation_result['phi_detected'].extend(matches)
            
            # Calculate text reduction ratio
            original_length = len(original_text)
            deidentified_length = len(deidentified_text)
            
            if original_length > 0:
                validation_result['reduction_ratio'] = (original_length - deidentified_length) / original_length
            
            # Check for common PHI indicators that might have been missed
            phi_indicators = ['DOB', 'SSN', '@', 'phone', 'address', 'born on']
            remaining_indicators = [
                indicator for indicator in phi_indicators 
                if indicator.lower() in deidentified_text.lower()
            ]
            
            if remaining_indicators:
                validation_result['issues'].append(f"PHI indicators still present: {remaining_indicators}")
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            validation_result['is_valid'] = False
            validation_result['issues'].append(f"Validation error: {str(e)}")
        
        return validation_result 