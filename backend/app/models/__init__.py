from app.models.association import (
    role_permissions,
    user_roles,
)

from app.models.audit_log import AuditLog

# Structured symptoms
from app.models.symptom import (
    Symptom,
    consultation_symptoms,
)

from app.models.consultation import Consultation
from app.models.consultation_medicine import ConsultationMedicine

from app.models.disease import Disease
from app.models.disease_case import DiseaseCase

from app.models.inventory_transaction import InventoryTransaction
from app.models.medicine import Medicine

from app.models.patient import Patient
from app.models.patient_history import PatientMedicalHistory

from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


__all__ = [
    # Authentication / RBAC
    "User",
    "Role",
    "Permission",
    "user_roles",
    "role_permissions",
    "AuditLog",

    # Patients
    "Patient",
    "PatientMedicalHistory",

    # Consultations
    "Consultation",
    "ConsultationMedicine",

    # Structured Symptoms
    "Symptom",
    "consultation_symptoms",

    # Diseases / Surveillance
    "Disease",
    "DiseaseCase",

    # Medicine / Inventory
    "Medicine",
    "InventoryTransaction",
]