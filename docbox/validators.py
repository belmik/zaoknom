from django.core.validators import RegexValidator

validate_phone = RegexValidator(
    regex=r"^\d{10}$", message="Номер должен состоять из десяти цифр."
)
