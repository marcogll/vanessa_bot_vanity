import os
import json
import logging
import requests
from datetime import datetime, time as time_cls

from modules.database import SessionVanityHr, register_user
from modules.ui import main_actions_keyboard
# from models.vanity_hr_models import HorarioEmpleadas, DataEmpleadas (Removed)

WEBHOOK_ONBOARDING_URLS = [
    w.strip()
    for w in (
        os.getenv("WEBHOOK_ONBOARDING") or os.getenv("WEBHOOK_CONTRATO") or ""
    ).split(",")
    if w and w.strip()
]

BOT_VERSION = os.getenv("ONBOARDING_BOT_VERSION", "welcome2soul_v2")

MAPA_MESES = {
    "Enero": "01",
    "Febrero": "02",
    "Marzo": "03",
    "Abril": "04",
    "Mayo": "05",
    "Junio": "06",
    "Julio": "07",
    "Agosto": "08",
    "Septiembre": "09",
    "Octubre": "10",
    "Noviembre": "11",
    "Diciembre": "12",
}

MAPA_SUCURSALES = {
    "Plaza Cima (Sur)": "plaza_cima",
    "Plaza O (Carranza)": "plaza_o",
}

DEFAULT_MESSAGES = {
    "horario": {
        "success": "¡Horario guardado con éxito! 👍",
        "error": "Ocurrió un error al guardar tu horario. Por favor, contacta a un administrador.",
    },
    "default": {
        "success": "Flujo completado correctamente.",
        "error": "Ocurrió un error al completar el flujo. Intenta nuevamente o contacta a un administrador.",
    },
}


def _clean_text(text: str) -> str:
    if text is None:
        return ""
    return " ".join(str(text).split())


def _normalize_id(value: str) -> str:
    if not value:
        return "N/A"
    cleaned = "".join(str(value).split()).upper()
    return "N/A" if cleaned in {"", "0"} else cleaned


def _num_to_words_es_hasta_999(n: int) -> str:
    if n < 0 or n > 999:
        return str(n)
    unidades = [
        "cero",
        "uno",
        "dos",
        "tres",
        "cuatro",
        "cinco",
        "seis",
        "siete",
        "ocho",
        "nueve",
    ]
    especiales = {
        10: "diez",
        11: "once",
        12: "doce",
        13: "trece",
        14: "catorce",
        15: "quince",
        20: "veinte",
        30: "treinta",
        40: "cuarenta",
        50: "cincuenta",
        60: "sesenta",
        70: "setenta",
        80: "ochenta",
        90: "noventa",
        100: "cien",
        200: "doscientos",
        300: "trescientos",
        400: "cuatrocientos",
        500: "quinientos",
        600: "seiscientos",
        700: "setecientos",
        800: "ochocientos",
        900: "novecientos",
    }
    if n < 10:
        return unidades[n]
    if n in especiales:
        return especiales[n]
    if n < 20:
        return "dieci" + unidades[n - 10]
    if n < 30:
        return "veinti" + unidades[n - 20]
    if n < 100:
        decenas = (n // 10) * 10
        resto = n % 10
        return f"{especiales[decenas]} y {unidades[resto]}"
    centenas = (n // 100) * 100
    resto = n % 100
    prefijo = (
        "ciento"
        if centenas == 100 and resto > 0
        else especiales.get(centenas, str(centenas))
    )
    if resto == 0:
        return prefijo
    return f"{prefijo} {_num_to_words_es_hasta_999(resto)}"


def numero_a_texto(num_ext: str, num_int: str) -> str:
    import re

    texto_base = _clean_text(num_ext)
    interior = _clean_text(num_int)
    match = re.match(r"(\d+)", texto_base)
    if not match:
        return texto_base
    numero = int(match.group(1))
    en_letras = _num_to_words_es_hasta_999(numero)
    if interior and interior.lower() not in {"", "n/a"}:
        return f"{en_letras}, interior {interior}".strip()
    return en_letras


def _extract_responses(data: dict) -> dict:
    reserved = {"flow_name", "current_state"}
    return {
        key: value
        for key, value in data.items()
        if key not in reserved and not str(key).startswith("_")
    }


def _month_to_number(value: str) -> str:
    return MAPA_MESES.get(value, value or "01")


def _resolve_other(responses: dict, key: str, other_key: str) -> str:
    value = responses.get(key, "N/A")
    if value in {"Otro", "Otra"}:
        other = _clean_text(responses.get(other_key, value))
        return other or value
    return value


def _build_date(year: str, month: str, day: str) -> str:
    try:
        day_num = str(day).zfill(2)
        month_num = _month_to_number(month)
        return f"{year}-{month_num}-{day_num}"
    except Exception:
        return "ERROR_FECHA"


def _prepare_onboarding_payload(responses: dict, meta: dict) -> dict:
    r = {
        key: _clean_text(value) if isinstance(value, str) else value
        for key, value in responses.items()
    }
    r["RFC"] = _normalize_id(r.get("RFC"))
    r["CURP"] = _normalize_id(r.get("CURP"))

    fecha_nac = _build_date(
        r.get("CUMPLE_ANIO", "0000"),
        r.get("CUMPLE_MES", "01"),
        r.get("CUMPLE_DIA", "01"),
    )
    fecha_ini = _build_date(
        r.get("INICIO_ANIO", "0000"),
        r.get("INICIO_MES", "01"),
        r.get("INICIO_DIA", "01"),
    )

    estado_nacimiento = _resolve_other(r, "ESTADO_NACIMIENTO", "ESTADO_NACIMIENTO_OTRO")
    ciudad_residencia = _resolve_other(r, "CIUDAD_RESIDENCIA", "CIUDAD_RESIDENCIA_OTRO")
    emergencia_relacion = _resolve_other(
        r, "EMERGENCIA_RELACION", "EMERGENCIA_RELACION_OTRA"
    )

    referencias = []
    for idx in range(1, 4):
        nombre = r.get(f"REF{idx}_NOMBRE", "N/A")
        telefono = r.get(f"REF{idx}_TELEFONO", "N/A")
        relacion = _resolve_other(r, f"REF{idx}_TIPO", f"REF{idx}_TIPO_OTRA")
        referencias.append(
            {"nombre": nombre, "telefono": telefono, "relacion": relacion}
        )

    num_ext_texto = numero_a_texto(r.get("NUM_EXTERIOR", ""), r.get("NUM_INTERIOR", ""))
    sucursal_id = MAPA_SUCURSALES.get(r.get("SUCURSAL"), "otra_sucursal")

    curp_val = r.get("CURP", "XXXX000000")
    curp_prefijo = curp_val[:4] if len(curp_val) >= 4 else "XXXX"
    try:
        fecha_inicio_dt = datetime.strptime(fecha_ini, "%Y-%m-%d")
        numero_empleado = f"{curp_prefijo}{fecha_inicio_dt.strftime('%y%m%d')}"
    except Exception:
        fecha_compacta = fecha_ini.replace("-", "")
        sufijo = (
            fecha_compacta[-6:] if len(fecha_compacta) >= 6 else fecha_compacta or "N/A"
        )
        numero_empleado = f"{curp_prefijo}{sufijo}"

    now = datetime.now()
    start_ts = meta.get("start_ts", now.timestamp())
    metadata_block = {
        "telegram_id": meta.get("telegram_id"),
        "username": meta.get("username"),
        "first_name": meta.get("first_name"),
        "chat_id": meta.get("telegram_id"),
        "bot_version": BOT_VERSION,
        "fecha_registro": now.isoformat(),
        "duracion_segundos": round(now.timestamp() - start_ts, 2),
        "mensajes_totales": meta.get("msg_count", 0),
    }

    payload = {
        "candidato": {
            "nombre_preferido": r.get("NOMBRE_SALUDO"),
            "nombre_oficial": r.get("NOMBRE_COMPLETO"),
            "apellido_paterno": r.get("APELLIDO_PATERNO"),
            "apellido_materno": r.get("APELLIDO_MATERNO"),
            "fecha_nacimiento": fecha_nac,
            "rfc": r.get("RFC"),
            "curp": r.get("CURP"),
            "lugar_nacimiento": estado_nacimiento,
        },
        "contacto": {
            "email": r.get("CORREO"),
            "celular": r.get("CELULAR"),
        },
        "domicilio": {
            "calle": r.get("CALLE"),
            "num_ext": r.get("NUM_EXTERIOR"),
            "num_int": r.get("NUM_INTERIOR"),
            "num_ext_texto": num_ext_texto,
            "colonia": r.get("COLONIA"),
            "cp": r.get("CODIGO_POSTAL"),
            "ciudad": ciudad_residencia,
            "estado": "Coahuila de Zaragoza",
        },
        "laboral": {
            "rol_id": _clean_text(r.get("ROL")).lower() or "n/a",
            "sucursal_id": sucursal_id,
            "fecha_inicio": fecha_ini,
            "numero_empleado": numero_empleado,
        },
        "referencias": referencias,
        "emergencia": {
            "nombre": r.get("EMERGENCIA_NOMBRE"),
            "telefono": r.get("EMERGENCIA_TEL"),
            "relacion": emergencia_relacion,
        },
        "metadata": metadata_block,
    }

    return payload


def _send_webhook(url: str, payload: dict):
    """Sends a POST request to a webhook."""
    if not url:
        logging.warning("No webhook URL provided.")
        return False
    try:
        headers = {"Content-Type": "application/json"}
        res = requests.post(url, json=payload, headers=headers, timeout=20)
        res.raise_for_status()
        logging.info(f"Webhook sent successfully to: {url}")
        return True
    except Exception as e:
        logging.error(f"Error sending webhook to {url}: {e}")
        return False


def _convert_to_time(time_str: str):
    """Converts a string like '10:00 AM' to a datetime.time object."""
    if not time_str or not isinstance(time_str, str):
        return None
    try:
        # Handle 'Todo el día' or other non-time strings
        if ":" not in time_str:
            return None
        return datetime.strptime(time_str, "%I:%M %p").time()
    except ValueError:
        logging.warning(f"Could not parse time string: {time_str}")
        return None


def _finalize_horario(telegram_id: int, data: dict):
    """Finalizes the 'horario' flow."""
    logging.info(f"Finalizing 'horario' flow for telegram_id: {telegram_id}")

    # 1. Prepare data for webhook and DB
    day_pairs = [
        ("monday", "MONDAY_IN", "MONDAY_OUT"),
        ("tuesday", "TUESDAY_IN", "TUESDAY_OUT"),
        ("wednesday", "WEDNESDAY_IN", "WEDNESDAY_OUT"),
        ("thursday", "THURSDAY_IN", "THURSDAY_OUT"),
        ("friday", "FRIDAY_IN", "FRIDAY_OUT"),
        ("saturday", "SATURDAY_IN", None),
    ]

    schedule_data = {
        "telegram_id": telegram_id,
        "short_name": data.get("SHORT_NAME"),
    }

    rows_for_db = []
    for day_key, in_key, out_key in day_pairs:
        entrada = _convert_to_time(data.get(in_key))
        salida_raw = data.get(out_key) if out_key else "6:00 PM"
        salida = _convert_to_time(salida_raw)

        schedule_data[f"{day_key}_in"] = entrada
        schedule_data[f"{day_key}_out"] = salida

        if not entrada or not salida:
            logging.warning(
                f"Missing schedule data for {day_key}. Entrada: {entrada}, Salida: {salida}"
            )
            continue

        rows_for_db.append(
            {
                "dia_semana": day_key,
                "hora_entrada": entrada,
                "hora_salida": salida,
            }
        )

    # 2. Send to webhook
    webhook_url = os.getenv("WEBHOOK_SCHEDULE")
    if webhook_url:
        json_payload = {
            k: (v.isoformat() if isinstance(v, time_cls) else v)
            for k, v in schedule_data.items()
        }
        json_payload["timestamp"] = datetime.now().isoformat()
        _send_webhook(webhook_url, json_payload)

    # 3. Save to database (vanity_hr.horario_empleadas)
    # Disabled temporarily as DB is removed
    if SessionVanityHr:
        logging.warning(
            "SessionVanityHr is present but DB logic is disabled in finalizer."
        )

    return True


def _finalize_onboarding(telegram_id: int, data: dict):
    """Finalizes the onboarding flow using declarative responses."""
    logging.info("Finalizing 'onboarding' flow for telegram_id: %s", telegram_id)

    responses = _extract_responses(data)
    meta = data.get("_meta", {})

    if not responses:
        logging.error("No responses captured for onboarding flow.")
        return {
            "success": False,
            "message_error": "⚠️ No pude leer tus respuestas. Por favor, intenta /registro de nuevo.",
            "reply_markup": main_actions_keyboard(),
        }

    payload = _prepare_onboarding_payload(responses, meta)
    meta_for_db = dict(meta)
    meta_for_db.update(
        {
            "msg_count": meta.get("msg_count", 0),
            "bot_version": BOT_VERSION,
        }
    )
    meta_for_db.setdefault("telegram_id", telegram_id)
    meta_for_db.setdefault("flow_name", data.get("flow_name"))
    metadata_block = payload.get("metadata", {})
    if metadata_block:
        meta_for_db.setdefault("fecha_registro", metadata_block.get("fecha_registro"))
        meta_for_db["duracion_segundos"] = metadata_block.get("duracion_segundos")

    enviados = 0
    for url in WEBHOOK_ONBOARDING_URLS:
        if _send_webhook(url, payload):
            enviados += 1

    try:
        db_ok = register_user({"meta": meta_for_db, **payload})
    except Exception as exc:
        logging.error("Error registrando usuaria en DB: %s", exc)
        db_ok = False

    if not db_ok:
        return {
            "success": False,
            "message_error": (
                "⚠️ Hubo un problema guardando tu registro. RH ya fue notificado; inténtalo más tarde."
            ),
            "reply_markup": main_actions_keyboard(),
        }

    if enviados:
        success_message = (
            "✅ *¡Registro exitoso!*\n\n"
            "Bienvenida a la familia Soul/Vanity. Tu contrato se está generando y te avisaremos pronto.\n"
            "¡Nos vemos el primer día! ✨"
        )
    else:
        success_message = (
            "⚠️ Se guardaron tus datos, pero no pude notificar al webhook. RH lo revisará manualmente.\n"
            "Si necesitas confirmar algo, contacta a tu manager."
        )

    return {
        "success": True,
        "message_success": success_message,
        "reply_markup": main_actions_keyboard(),
    }


# Mapping of flow names to finalization functions
FINALIZATION_MAP = {
    "horario": _finalize_horario,
    "onboarding": _finalize_onboarding,
}


async def finalize_flow(update, context):
    """Generic function to finalize a conversation flow."""
    flow_name = context.user_data.get("flow_name")
    telegram_id = update.effective_user.id

    if not flow_name:
        logging.error("finalize_flow called without a flow_name in user_data.")
        return

    finalizer_func = FINALIZATION_MAP.get(flow_name)
    if not finalizer_func:
        logging.warning(f"No finalizer function found for flow: {flow_name}")
        await update.message.reply_text("Flujo completado (sin acción final definida).")
        return

    # The final answer needs to be saved first
    current_state_key = context.user_data.get("current_state")
    if current_state_key is not None:
        flow_definition_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "conv-flows",
            f"{flow_name}.json",
        )
        with open(flow_definition_path, "r") as f:
            flow = json.load(f)
        current_step = next(
            (step for step in flow["steps"] if step["state"] == current_state_key), None
        )
        if current_step and current_step.get("type") != "info":
            variable_name = current_step.get("variable")
            if variable_name:
                context.user_data[variable_name] = update.message.text

    result = finalizer_func(telegram_id, context.user_data)

    reply_markup = None
    if isinstance(result, dict):
        success = result.get("success", True)
        message = (
            result.get("message_success") if success else result.get("message_error")
        )
        reply_markup = result.get("reply_markup")
    else:
        success = bool(result)
        message = None

    defaults = DEFAULT_MESSAGES.get(flow_name, DEFAULT_MESSAGES["default"])
    if not message:
        message = defaults["success"] if success else defaults["error"]

    await update.message.reply_text(message, reply_markup=reply_markup)
    context.user_data.clear()
