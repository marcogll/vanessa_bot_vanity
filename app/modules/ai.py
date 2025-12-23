import os
import importlib
import importlib.metadata as importlib_metadata

# Compatibilidad para entornos donde packages_distributions no existe (p.ej. Python 3.9 con importlib recortado).
if not hasattr(importlib_metadata, "packages_distributions"):
    try:
        import importlib_metadata as backport_metadata  # type: ignore
        if hasattr(backport_metadata, "packages_distributions"):
            importlib_metadata.packages_distributions = backport_metadata.packages_distributions  # type: ignore[attr-defined]
        else:
            importlib_metadata.packages_distributions = lambda: {}  # type: ignore[assignment]
    except Exception:
        importlib_metadata.packages_distributions = lambda: {}  # type: ignore[assignment]

import google.generativeai as genai

def classify_reason(text: str) -> str:
    """
    Clasifica el motivo de un permiso utilizando la API de Gemini.

    Args:
        text: El motivo del permiso proporcionado por el usuario.

    Returns:
        La categoría clasificada (EMERGENCIA, MÉDICO, TRÁMITE, PERSONAL) o "OTRO" si no se puede clasificar.
    """
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""
        Clasifica el siguiente motivo de solicitud de permiso en una de estas cuatro categorías: EMERGENCIA, MÉDICO, TRÁMITE, PERSONAL.
        Responde únicamente con la palabra de la categoría en mayúsculas.

        Motivo: "{text}"
        Categoría:
        """

        response = model.generate_content(prompt)
        
        # Limpiar la respuesta para obtener solo la categoría
        category = response.text.strip().upper()

        # Validar que la categoría sea una de las esperadas
        valid_categories = ["EMERGENCIA", "MÉDICO", "TRÁMITE", "PERSONAL"]
        if category in valid_categories:
            return category
        else:
            return "PERSONAL" # Si la IA devuelve algo inesperado, se asigna a PERSONAL

    except Exception as e:
        print(f"Error al clasificar con IA: {e}")
        return "PERSONAL" # En caso de error, se asigna a PERSONAL por defecto
