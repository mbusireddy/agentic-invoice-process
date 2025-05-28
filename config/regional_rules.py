"""
Regional rules and regulations for invoice processing
"""
from typing import Dict, List, Any
from enum import Enum


class Region(Enum):
    US = "US"
    EU = "EU"
    APAC = "APAC"
    LATAM = "LATAM"


class TaxType(Enum):
    VAT = "VAT"
    GST = "GST"
    SALES_TAX = "SALES_TAX"
    SERVICE_TAX = "SERVICE_TAX"


# Regional Rules Configuration
REGIONAL_RULES = {
    Region.US.value: {
        "currency": ["USD"],
        "tax_types": [TaxType.SALES_TAX.value],
        "tax_rates": {
            "standard": 0.08,
            "reduced": 0.05,
            "exempt": 0.0
        },
        "required_fields": [
            "invoice_number",
            "date",
            "vendor_name",
            "vendor_address",
            "buyer_name",
            "buyer_address",
            "line_items",
            "subtotal",
            "tax_amount",
            "total_amount"
        ],
        "date_format": "MM/DD/YYYY",
        "amount_validation": {
            "max_amount": 50000.0,
            "min_amount": 0.01
        },
        "vendor_validation": {
            "require_tax_id": True,
            "tax_id_format": r"^\d{2}-\d{7}$"
        },
        "approval_rules": {
            "auto_approve_limit": 1000.0,
            "manager_approval_limit": 10000.0,
            "executive_approval_limit": 50000.0
        }
    },

    Region.EU.value: {
        "currency": ["EUR", "GBP", "CHF"],
        "tax_types": [TaxType.VAT.value],
        "tax_rates": {
            "standard": 0.20,
            "reduced": 0.10,
            "exempt": 0.0
        },
        "required_fields": [
            "invoice_number",
            "date",
            "vendor_name",
            "vendor_address",
            "vendor_vat_number",
            "buyer_name",
            "buyer_address",
            "buyer_vat_number",
            "line_items",
            "subtotal",
            "vat_amount",
            "total_amount"
        ],
        "date_format": "DD/MM/YYYY",
        "amount_validation": {
            "max_amount": 45000.0,
            "min_amount": 0.01
        },
        "vendor_validation": {
            "require_vat_number": True,
            "vat_number_format": r"^[A-Z]{2}\d{8,12}$"
        },
        "approval_rules": {
            "auto_approve_limit": 900.0,
            "manager_approval_limit": 9000.0,
            "executive_approval_limit": 45000.0
        }
    },

    Region.APAC.value: {
        "currency": ["INR", "SGD", "AUD", "JPY"],
        "tax_types": [TaxType.GST.value, TaxType.SERVICE_TAX.value],
        "tax_rates": {
            "standard": 0.18,
            "reduced": 0.05,
            "exempt": 0.0
        },
        "required_fields": [
            "invoice_number",
            "date",
            "vendor_name",
            "vendor_address",
            "vendor_gstin",
            "buyer_name",
            "buyer_address",
            "buyer_gstin",
            "line_items",
            "subtotal",
            "tax_amount",
            "total_amount"
        ],
        "date_format": "DD-MM-YYYY",
        "amount_validation": {
            "max_amount": 3500000.0,  # Approx 42k USD
            "min_amount": 1.0
        },
        "vendor_validation": {
            "require_gstin": True,
            "gstin_format": r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$"
        },
        "approval_rules": {
            "auto_approve_limit": 75000.0,  # Approx 900 USD
            "manager_approval_limit": 750000.0,  # Approx 9k USD
            "executive_approval_limit": 3500000.0  # Approx 42k USD
        }
    },

    Region.LATAM.value: {
        "currency": ["BRL", "MXN", "COP", "CLP"],
        "tax_types": [TaxType.VAT.value, TaxType.SERVICE_TAX.value],
        "tax_rates": {
            "standard": 0.16,
            "reduced": 0.08,
            "exempt": 0.0
        },
        "required_fields": [
            "invoice_number",
            "date",
            "vendor_name",
            "vendor_address",
            "vendor_tax_id",
            "buyer_name",
            "buyer_address",
            "line_items",
            "subtotal",
            "tax_amount",
            "total_amount"
        ],
        "date_format": "DD/MM/YYYY",
        "amount_validation": {
            "max_amount": 250000.0,
            "min_amount": 0.01
        },
        "vendor_validation": {
            "require_tax_id": True,
            "tax_id_format": r"^\d{8,14}$"
        },
        "approval_rules": {
            "auto_approve_limit": 5000.0,
            "manager_approval_limit": 50000.0,
            "executive_approval_limit": 250000.0
        }
    }
}

# Validation Rules
VALIDATION_RULES = {
    "common": {
        "invoice_number": {
            "required": True,
            "max_length": 50,
            "pattern": r"^[A-Za-z0-9\-_/]+$"
        },
        "date": {
            "required": True,
            "max_age_days": 365,
            "future_date_allowed": False
        },
        "amounts": {
            "precision": 2,
            "allow_negative": False,
            "require_currency": True
        },
        "vendor_name": {
            "required": True,
            "min_length": 2,
            "max_length": 200
        },
        "line_items": {
            "min_items": 1,
            "max_items": 100,
            "required_fields": ["description", "quantity", "unit_price", "total"]
        }
    },
    "calculations": {
        "tolerance": 0.01,  # Allowed difference in calculations
        "check_line_totals": True,
        "check_tax_calculations": True,
        "check_grand_total": True
    }
}


def get_regional_rules(region: str) -> Dict[str, Any]:
    """Get rules for a specific region"""
    return REGIONAL_RULES.get(region, REGIONAL_RULES[Region.US.value])


def get_validation_rules() -> Dict[str, Any]:
    """Get general validation rules"""
    return VALIDATION_RULES


def get_supported_currencies(region: str) -> List[str]:
    """Get supported currencies for a region"""
    rules = get_regional_rules(region)
    return rules.get("currency", ["USD"])


def get_tax_types(region: str) -> List[str]:
    """Get supported tax types for a region"""
    rules = get_regional_rules(region)
    return rules.get("tax_types", [TaxType.SALES_TAX.value])


def get_approval_limits(region: str) -> Dict[str, float]:
    """Get approval limits for a region"""
    rules = get_regional_rules(region)
    return rules.get("approval_rules", {})


def validate_region(region: str) -> bool:
    """Validate if region is supported"""
    return region in [r.value for r in Region]