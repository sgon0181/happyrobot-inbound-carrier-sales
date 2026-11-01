"""FMCSA assessment ported from the exercised native and Fly integration."""

import json
import re
import urllib.request
import urllib.error
import urllib.parse
from service.core.ports import TmsUnavailable

SafetyError = ValueError


class IntegrationError(TmsUnavailable):
    def __init__(self, message, code="FMCSA_UNAVAILABLE", retryable=False):
        self.code = code
        super().__init__(code)


class FMCSAClient:
    BASE = "https://mobile.fmcsa.dot.gov/qc/services"
    MAX_JSON = 2 * 1024 * 1024

    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def normalize_mc(mc):
        value = re.sub(r"^MC[ -]*", "", str(mc).strip(), flags=re.I)
        if not re.fullmatch(r"[0-9]{1,8}", value):
            raise SafetyError("MC must contain one to eight digits with an optional MC prefix")
        return str(int(value))

    def _get_json(self, suffix):
        if not self.settings.fmcsa_api_key:
            raise IntegrationError("FMCSA_API_KEY is not configured", "FMCSA_NOT_CONFIGURED")
        url = (
            self.BASE
            + suffix
            + "?"
            + urllib.parse.urlencode({"webKey": self.settings.fmcsa_api_key})
        )
        request = urllib.request.Request(
            url, headers={"Accept": "application/json", "User-Agent": "isolated-fde-harness/1"}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.settings.timeout) as response:
                data = response.read(self.MAX_JSON + 1)
                if len(data) > self.MAX_JSON:
                    raise IntegrationError(
                        "FMCSA response exceeds the size bound", "FMCSA_MALFORMED"
                    )
            result = json.loads(data)
        except urllib.error.HTTPError as error:
            status = error.code
            error.close()
            if status == 404:
                return {"content": []}
            raise IntegrationError(
                "FMCSA request failed (HTTP " + str(status) + ")", "FMCSA_HTTP_ERROR"
            ) from None
        except (OSError, ValueError, UnicodeError):
            raise IntegrationError(
                "FMCSA response unavailable or malformed", "FMCSA_UNAVAILABLE"
            ) from None
        if not isinstance(result, dict):
            raise IntegrationError("FMCSA response has an unexpected shape", "FMCSA_MALFORMED")
        return result

    @staticmethod
    def _carriers(payload):
        content = payload.get("content")
        if content in (None, []):
            return []
        if isinstance(content, dict):
            content = [content]
        if not isinstance(content, list):
            raise IntegrationError(
                "FMCSA carrier response has an unexpected shape", "FMCSA_MALFORMED"
            )
        carriers = []
        for item in content:
            if not isinstance(item, dict) or not isinstance(item.get("carrier"), dict):
                raise IntegrationError(
                    "FMCSA carrier record has an unexpected shape", "FMCSA_MALFORMED"
                )
            carriers.append(item["carrier"])
        return carriers

    @staticmethod
    def assess(carrier):
        """Assess a snapshot using explicit positive signals, with no missing-data pass.

        Official element docs define Y/N operate/OOS flags and OOS date semantics.
        The live QCMobile carrier representation instead includes statusCode and
        oosDate. For that observed shape, accept an explicitly null date only
        together with active registration, permission and active carrier authority.
        Null or missing data alone never establishes eligibility.
        """

        def signal(value):
            return value.upper() if isinstance(value, str) and len(value) <= 16 else None

        allowed = signal(carrier.get("allowedToOperate", carrier.get("allowToOperate")))
        common = signal(carrier.get("commonAuthorityStatus"))
        contract = signal(carrier.get("contractAuthorityStatus"))
        out_of_service = signal(carrier.get("outOfService"))
        registration = signal(carrier.get("statusCode"))
        signals = {
            "allowed_to_operate": allowed,
            "common_authority": common,
            "contract_authority": contract,
            "out_of_service": out_of_service,
            "registration_status": registration,
            "out_of_service_basis": None,
        }
        if registration in {"I", "INACTIVE"}:
            return False, "registration_inactive", signals
        if registration in {"O", "OOS", "OUT_OF_SERVICE", "OUT-OF-SERVICE"}:
            return False, "out_of_service", signals
        if registration is not None and registration not in {"A", "ACTIVE"}:
            return False, "registration_status_unverified", signals
        if allowed == "N":
            return False, "not_allowed_to_operate", signals
        if out_of_service == "Y" or carrier.get("oosDate") or carrier.get("outOfServiceDate"):
            return False, "out_of_service", signals
        active = common in {"A", "ACTIVE"} or contract in {"A", "ACTIVE"}
        if not active:
            return False, "carrier_authority_inactive_or_unverified", signals
        if allowed != "Y":
            return False, "permission_to_operate_unverified", signals
        if out_of_service == "N":
            signals["out_of_service_basis"] = "explicit_flag"
        elif (
            out_of_service is None
            and registration in {"A", "ACTIVE"}
            and (
                ("oosDate" in carrier and carrier["oosDate"] is None)
                or ("outOfServiceDate" in carrier and carrier["outOfServiceDate"] is None)
            )
        ):
            signals["out_of_service_basis"] = "active_registration_and_explicit_null_oos_date"
        else:
            return False, "out_of_service_status_unverified", signals
        return True, "active_carrier_authority_verified", signals

    def assess_payload(self, payload, mc):
        """Apply the same policy to an actual payload obtained by native egress.

        This does not fetch data, validate a caller's identity, or override any
        authority signal. It supports documented alternate HTTP transports.
        """
        normalized = self.normalize_mc(mc)
        if not isinstance(payload, dict):
            raise IntegrationError("FMCSA response has an unexpected shape", "FMCSA_MALFORMED")
        if "content" not in payload or any(
            key in payload for key in ["error", "errorMessage", "exception"]
        ):
            raise IntegrationError("FMCSA returned an application error", "FMCSA_APPLICATION_ERROR")
        carriers = self._carriers(payload)
        if not carriers:
            return {
                "mc": normalized,
                "eligible": False,
                "carrier": None,
                "reason": "not_found",
                "signals": {},
            }
        if len(carriers) != 1:
            return {
                "mc": normalized,
                "eligible": False,
                "carrier": None,
                "reason": "ambiguous_carrier_match",
                "signals": {},
            }
        carrier = carriers[0]
        eligible, reason, signals = self.assess(carrier)
        # Return a minimal public-data summary, not contact details or webkey.
        public = {
            key: carrier[key] for key in ["dotNumber", "legalName", "dbaName"] if key in carrier
        }
        for mapping in (public, signals):
            for key, value in mapping.items():
                if isinstance(value, str) and self.settings.fmcsa_api_key:
                    mapping[key] = value.replace(self.settings.fmcsa_api_key, "[SECRET HIDDEN]")
        return {
            "mc": normalized,
            "eligible": eligible,
            "carrier": public,
            "reason": reason,
            "signals": signals,
        }

    def lookup(self, mc):
        normalized = self.normalize_mc(mc)
        payload = self._get_json("/carriers/docket-number/" + normalized + "/")
        return self.assess_payload(payload, normalized)
