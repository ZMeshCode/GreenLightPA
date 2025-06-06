"""
FHIR Bundle Processing Service
Extracts clinical notes and medical codes from FHIR bundles
"""

import json
import logging
import re
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FHIRProcessor:
    """Service for processing FHIR bundles and extracting clinical data"""
    
    def __init__(self):
        self.specialty_mappings = {
            "363346000": "oncology",  # Malignant neoplastic disease
            "69896004": "rheumatology",  # Rheumatoid arthritis
            "439401001": "radiology",  # Diagnostic imaging
        }
    
    def extract_clinical_notes(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract clinical notes from FHIR bundle
        
        Args:
            bundle: FHIR bundle dictionary
            
        Returns:
            List of clinical note dictionaries
        """
        notes = []
        patient_id = self._extract_patient_id(bundle)
        
        try:
            for entry in bundle.get('entry', []):
                resource = entry.get('resource', {})
                resource_type = resource.get('resourceType')
                
                # Process DocumentReference resources (clinical notes)
                if resource_type == 'DocumentReference':
                    note = self._process_document_reference(resource, patient_id)
                    if note:
                        notes.append(note)
                
                # Process DiagnosticReport resources
                elif resource_type == 'DiagnosticReport':
                    note = self._process_diagnostic_report(resource, patient_id)
                    if note:
                        notes.append(note)
                
                # Process Observation resources for prior auth status
                elif resource_type == 'Observation':
                    self._extract_prior_auth_status(resource, notes, patient_id)
            
            # Extract medical codes for all notes
            for note in notes:
                note['extracted_codes'] = self._extract_medical_codes(bundle)
                note['specialty'] = self._determine_specialty(note['extracted_codes'])
                
        except Exception as e:
            logger.error(f"Error extracting clinical notes from bundle: {e}")
        
        logger.info(f"Extracted {len(notes)} clinical notes for patient {patient_id}")
        return notes
    
    def _extract_patient_id(self, bundle: Dict[str, Any]) -> str:
        """Extract patient ID from FHIR bundle"""
        try:
            for entry in bundle.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'Patient':
                    return resource.get('id', str(uuid.uuid4()))
            return str(uuid.uuid4())
        except Exception:
            return str(uuid.uuid4())
    
    def _process_document_reference(self, resource: Dict[str, Any], patient_id: str) -> Optional[Dict[str, Any]]:
        """Process DocumentReference resource to extract clinical note"""
        try:
            # Extract text content
            content = resource.get('content', [])
            if not content:
                return None
            
            # Get the first attachment with text data
            attachment = content[0].get('attachment', {})
            text_data = attachment.get('data') or attachment.get('url', '')
            
            if not text_data:
                return None
            
            # Create note record
            note = {
                'note_id': resource.get('id', str(uuid.uuid4())),
                'patient_id': patient_id,
                'text': text_data,
                'type': resource.get('type', {}).get('text', 'Clinical Note'),
                'date': resource.get('date', datetime.now().isoformat()),
                'prior_auth_required': False,
                'prior_auth_status': 'pending'
            }
            
            return note
            
        except Exception as e:
            logger.error(f"Error processing DocumentReference: {e}")
            return None
    
    def _process_diagnostic_report(self, resource: Dict[str, Any], patient_id: str) -> Optional[Dict[str, Any]]:
        """Process DiagnosticReport resource to extract clinical note"""
        try:
            # Extract conclusion or presentedForm text
            text_content = resource.get('conclusion', '')
            
            # If no conclusion, try to extract from presentedForm
            if not text_content:
                presented_forms = resource.get('presentedForm', [])
                for form in presented_forms:
                    if form.get('contentType') == 'text/plain':
                        text_content = form.get('data', '')
                        break
            
            if not text_content:
                return None
            
            # Create note record
            note = {
                'note_id': resource.get('id', str(uuid.uuid4())),
                'patient_id': patient_id,
                'text': text_content,
                'type': 'Diagnostic Report',
                'date': resource.get('effectiveDateTime', datetime.now().isoformat()),
                'prior_auth_required': False,
                'prior_auth_status': 'pending'
            }
            
            return note
            
        except Exception as e:
            logger.error(f"Error processing DiagnosticReport: {e}")
            return None
    
    def _extract_prior_auth_status(self, resource: Dict[str, Any], notes: List[Dict[str, Any]], patient_id: str):
        """Extract prior authorization status from Observation resources"""
        try:
            # Check if this is a prior auth observation
            code = resource.get('code', {})
            coding = code.get('coding', [])
            
            for code_entry in coding:
                if code_entry.get('code') == 'LA33-6':  # Prior Authorization Status
                    # Extract the status value
                    value_code = resource.get('valueCodeableConcept', {})
                    value_coding = value_code.get('coding', [])
                    
                    for value_entry in value_coding:
                        status_code = value_entry.get('code')
                        if status_code in ['373066001', '373067005']:  # Approved/Denied
                            status = 'approved' if status_code == '373066001' else 'denied'
                            
                            # Update all notes for this patient
                            for note in notes:
                                if note['patient_id'] == patient_id:
                                    note['prior_auth_required'] = True
                                    note['prior_auth_status'] = status
                            break
                    break
                    
        except Exception as e:
            logger.error(f"Error extracting prior auth status: {e}")
    
    def _extract_medical_codes(self, bundle: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract medical codes (ICD-10, CPT, SNOMED) from FHIR bundle"""
        codes = {
            'icd10': [],
            'cpt': [],
            'snomed': [],
            'hcpcs': [],
            'ndc': []
        }
        
        try:
            for entry in bundle.get('entry', []):
                resource = entry.get('resource', {})
                resource_type = resource.get('resourceType')
                
                # Extract codes from Condition resources
                if resource_type == 'Condition':
                    self._extract_codes_from_condition(resource, codes)
                
                # Extract codes from Procedure resources
                elif resource_type == 'Procedure':
                    self._extract_codes_from_procedure(resource, codes)
                
                # Extract codes from MedicationRequest resources
                elif resource_type == 'MedicationRequest':
                    self._extract_codes_from_medication(resource, codes)
                
        except Exception as e:
            logger.error(f"Error extracting medical codes: {e}")
        
        return codes
    
    def _extract_codes_from_condition(self, resource: Dict[str, Any], codes: Dict[str, List[str]]):
        """Extract codes from Condition resource"""
        try:
            code = resource.get('code', {})
            coding = code.get('coding', [])
            
            for code_entry in coding:
                system = code_entry.get('system', '')
                code_value = code_entry.get('code', '')
                
                if 'icd' in system.lower() and code_value:
                    codes['icd10'].append(code_value)
                elif 'snomed' in system.lower() and code_value:
                    codes['snomed'].append(code_value)
                    
        except Exception as e:
            logger.error(f"Error extracting codes from condition: {e}")
    
    def _extract_codes_from_procedure(self, resource: Dict[str, Any], codes: Dict[str, List[str]]):
        """Extract codes from Procedure resource"""
        try:
            code = resource.get('code', {})
            coding = code.get('coding', [])
            
            for code_entry in coding:
                system = code_entry.get('system', '')
                code_value = code_entry.get('code', '')
                
                if 'cpt' in system.lower() and code_value:
                    codes['cpt'].append(code_value)
                elif 'hcpcs' in system.lower() and code_value:
                    codes['hcpcs'].append(code_value)
                elif 'snomed' in system.lower() and code_value:
                    codes['snomed'].append(code_value)
                    
        except Exception as e:
            logger.error(f"Error extracting codes from procedure: {e}")
    
    def _extract_codes_from_medication(self, resource: Dict[str, Any], codes: Dict[str, List[str]]):
        """Extract codes from MedicationRequest resource"""
        try:
            medication = resource.get('medicationCodeableConcept', {})
            coding = medication.get('coding', [])
            
            for code_entry in coding:
                system = code_entry.get('system', '')
                code_value = code_entry.get('code', '')
                
                if 'ndc' in system.lower() and code_value:
                    codes['ndc'].append(code_value)
                    
        except Exception as e:
            logger.error(f"Error extracting codes from medication: {e}")
    
    def _determine_specialty(self, extracted_codes: Dict[str, List[str]]) -> str:
        """Determine medical specialty based on extracted codes"""
        try:
            # Check SNOMED codes for specialty indicators
            for snomed_code in extracted_codes.get('snomed', []):
                if snomed_code in self.specialty_mappings:
                    return self.specialty_mappings[snomed_code]
            
            # Default specialty based on code patterns
            all_codes = []
            for code_list in extracted_codes.values():
                all_codes.extend(code_list)
            
            code_text = ' '.join(all_codes).lower()
            
            if any(term in code_text for term in ['cancer', 'tumor', 'oncology', 'chemo']):
                return 'oncology'
            elif any(term in code_text for term in ['arthritis', 'rheum', 'joint']):
                return 'rheumatology'
            elif any(term in code_text for term in ['imaging', 'scan', 'mri', 'ct']):
                return 'radiology'
            else:
                return 'general'
                
        except Exception as e:
            logger.error(f"Error determining specialty: {e}")
            return 'general' 