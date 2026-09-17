"""BaseTab — eval helpers for dynamic variables in numeric fields."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ...controller.project_controller import ProjectController


class BaseTab:
    controller: Optional["ProjectController"] = None

    def bind_controller(self, controller: "ProjectController") -> None:
        self.controller = controller
        if hasattr(controller, "state_changed"):
            controller.state_changed.connect(self.on_state_changed)

    def on_state_changed(self) -> None:
        pass

    def _get_context(self) -> dict[str, Any]:
        if self.controller is None:
            return {}
        from ...utils.eval_context import build_eval_context
        return build_eval_context(self.controller.project)


    @staticmethod
    def _normalize_decimal(text: str) -> str:
        """Accept French/EU decimals (0,5 → 0.5) without turning commas into tuples.

        Rules:
        - pure number with one comma as decimal separator → replace by dot
        - thousand dots + decimal comma (1.234,56) → 1234.56
        - leave real expressions (function calls, identifiers) unchanged
        """
        s = (text or "").strip().replace(" ", "").replace("\u00a0", "")
        if not s:
            return s
        # expression with letters / operators other than . + - e E → don't touch
        # but allow leading +/- and exponent
        import re
        # EU: optional sign, digits, optional .thousands, decimal comma, digits
        m = re.fullmatch(r"([+-]?)(?:(\d{1,3}(?:\.\d{3})+)|(\d+)),(\d+)", s)
        if m:
            sign, grouped, plain, frac = m.group(1), m.group(2), m.group(3), m.group(4)
            intpart = (grouped or plain or "").replace(".", "")
            return f"{sign}{intpart}.{frac}"
        # simple 0,5 or ,5
        m = re.fullmatch(r"([+-]?)(\d*),(\d+)", s)
        if m:
            sign, a, b = m.group(1), m.group(2) or "0", m.group(3)
            return f"{sign}{a}.{b}"
        # US with thousands commas: 1,234.56
        m = re.fullmatch(r"([+-]?)(\d{1,3}(?:,\d{3})+)(\.\d+)?", s)
        if m:
            sign, grouped, frac = m.group(1), m.group(2), m.group(3) or ""
            return f"{sign}{grouped.replace(',', '')}{frac}"
        return text.strip()

    @staticmethod
    def _to_float(value: Any, field_name: str = "") -> float:
        """Coerce eval result to a scalar float (handles 0-d arrays, 1-tuples, etc.)."""
        if value is None:
            raise TypeError("expression returned None")
        # numpy scalar / 0-d array
        if hasattr(value, "item") and callable(value.item):
            try:
                value = value.item()
            except Exception:
                pass
        if isinstance(value, (list, tuple)):
            if len(value) == 1:
                return BaseTab._to_float(value[0], field_name)
            raise TypeError(
                f"expression returned a sequence {value!r} — "
                f"use a scalar here"
                + (f" (field '{field_name}')" if field_name else "")
                + ". For a centre, use avatar[i].x / .y, not .center"
            )
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            return float(value.strip())
        raise TypeError(
            f"cannot convert {type(value).__name__} {value!r} to float"
            + (f" (field '{field_name}')" if field_name else "")
        )

    def eval_float(self, text: str, default: float = 0.0, field_name: str = "") -> float:
        raw = (text or "").strip()
        if not raw:
            return default
        # EU decimal / thousand separators → ASCII form
        text = self._normalize_decimal(raw)
        # Pure numeric literal — fast path, no eval (avoids 0,0 → tuple)
        try:
            return float(text)
        except ValueError:
            pass
        try:
            from ...utils.safe_eval import safe_eval
            result = safe_eval(text, self._get_context())
            return self._to_float(result, field_name)
        except Exception as e:
            self._show_eval_error(raw, e, field_name)
            raise ValueError(str(e)) from e

    def eval_int(self, text: str, default: int = 0, field_name: str = "") -> int:
        return int(round(self.eval_float(text, float(default), field_name)))

    def eval_list(self, text: str, expected_length: int | None = None,
                  default: list | None = None, field_name: str = "") -> list:
        text = (text or "").strip()
        if not text:
            return list(default or [])
        from ...utils.safe_eval import safe_eval
        try:
            result = safe_eval(text, self._get_context())
            if isinstance(result, (list, tuple)):
                out = [float(x) for x in result]
            elif isinstance(result, (int, float)):
                out = [float(result)]
            elif "," in text:
                out = [float(safe_eval(p.strip(), self._get_context())) for p in text.split(",")]
            else:
                raise ValueError(f"cannot convert {text!r} to list")
            if expected_length is not None and len(out) != expected_length:
                raise ValueError(f"expected {expected_length} elements, got {len(out)}")
            return out
        except Exception as e:
            self._show_eval_error(text, e, field_name)
            raise

    def eval_dict(self, text: str, field_name: str = "") -> dict:
        """Parse key=val, key=val with nested expressions."""
        if not (text or "").strip():
            return {}
        from ...utils.safe_eval import safe_eval
        ctx = self._get_context()
        props: dict = {}
        current_key = None
        current_value = ""
        paren = bracket = 0
        in_quotes = False
        quote_char = None
        i = 0
        text = text.strip()
        try:
            while i < len(text):
                char = text[i]
                if char in ('"', "'") and (i == 0 or text[i - 1] != "\\"):
                    if not in_quotes:
                        in_quotes, quote_char = True, char
                    elif char == quote_char:
                        in_quotes, quote_char = False, None
                if in_quotes:
                    current_value += char
                    i += 1
                    continue
                if char == "(":
                    paren += 1
                elif char == ")":
                    paren -= 1
                elif char == "[":
                    bracket += 1
                elif char == "]":
                    bracket -= 1
                if char == "=" and current_key is None and paren == 0 and bracket == 0:
                    current_key = current_value.strip()
                    current_value = ""
                    i += 1
                    continue
                if char == "," and paren == 0 and bracket == 0 and current_key is not None:
                    vs = current_value.strip()
                    try:
                        props[current_key] = safe_eval(vs, ctx)
                    except Exception:
                        props[current_key] = vs.strip("'\"")
                    current_key = None
                    current_value = ""
                    i += 1
                    continue
                current_value += char
                i += 1
            if current_key is not None:
                vs = current_value.strip()
                try:
                    props[current_key] = safe_eval(vs, ctx)
                except Exception:
                    props[current_key] = vs.strip("'\"")
            return props
        except Exception as e:
            self._show_eval_error(text, e, field_name)
            raise

    def _show_eval_error(self, text: str, error: Exception, field_name: str = "") -> None:
        try:
            from PyQt6.QtWidgets import QMessageBox
            msg = "Expression invalide"
            if field_name:
                msg += f" pour '{field_name}'"
            msg += f":\n\n'{text}'\n\nErreur: {error}\n\n"
            dyn = {}
            if self.controller is not None:
                dyn = dict(self.controller.project.dynamic_vars)
            if dyn:
                msg += "Variables dynamiques:\n  " + "\n  ".join(list(dyn.keys())[:12])
            else:
                msg += "Aucune variable — Tools → Variables dynamiques (Ctrl+V)"
            msg += (
                "\n\nRéférences: avatar[i].x, group['nom'], "
                "material['n'].density, model['n'].dimension, "
                "avatars_by_color('BLUEx'), pi, sqrt, …"
            )
            QMessageBox.critical(self if hasattr(self, "window") else None, "Évaluation", msg)
        except Exception:
            pass

    def add_expression_help_label(self, layout) -> None:
        try:
            from PyQt6.QtWidgets import QLabel
            from ..styles import EXPR_HINT_HTML
            help_label = QLabel(EXPR_HINT_HTML)
            help_label.setObjectName("exprHint")
            help_label.setWordWrap(True)
            layout.addWidget(help_label)
        except Exception:
            try:
                from PyQt6.QtWidgets import QLabel
                help_label = QLabel(
                    "<span style='color:#1b7a4a'>Expressions : thickness, avatar[0].x, "
                    "group['mur'][0].y, 2*pi*r — Ctrl+V</span>"
                )
                help_label.setObjectName("exprHint")
                help_label.setWordWrap(True)
                layout.addWidget(help_label)
            except Exception:
                pass

    def mark_expr_field(self, widget) -> None:
        """Tint a QLineEdit as expression-capable (green border)."""
        try:
            widget.setProperty("exprField", True)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        except Exception:
            pass
