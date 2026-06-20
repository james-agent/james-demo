"""CRM database models."""

from crm_api.models.customer import Customer
from crm_api.models.q2_customer_sync import Q2CustomerSync

__all__ = ["Customer", "Q2CustomerSync"]
