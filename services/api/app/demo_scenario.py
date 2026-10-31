"""Phase 10: reproducible end-to-end demonstration driven only by the public API.

Run explicitly (never at startup), in local demo mode against a migrated and seeded
database::

    python -m app.demo_scenario            # in-process app, prints a result table
    python -m app.demo_scenario --json     # machine-readable summary on stdout
    python -m app.demo_scenario --base-url http://127.0.0.1:8000   # loopback server

All data is SYNTHETIC / DEMO DATA from ``samples/demo`` (ground truth in
``samples/demo/expected.json``). Nothing here edits the database directly: every
action is an HTTP call as one of the seeded demo accounts. Verification outcomes in
this prototype are SIMULATED; nothing is verified against any government system.

Re-running is safe: every run uploads new immutable batches and re-activates the
same final snapshots. On a database that already holds an earlier run the
informational (INFO) cross-institution matches and cumulative case signals that the
earlier run caused are reported as ``carryover`` instead of false positives.
"""

import argparse
import base64
import csv
import io
import json
import os
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
from openpyxl import Workbook
from pydantic import SecretStr, ValidationError

from app.core.config import Settings
from app.modules.submissions.parsing import HEADERS
from app.seed import seed_id

SAMPLES = Path(__file__).resolve().parents[3] / "samples" / "demo"
MANIFEST = SAMPLES / "expected.json"
API = "/api/v1"
YEAR = "2026-27"
PROGRAMME = "DEMO-COMP"
LABEL = "SIMULATED / DEMO DATA"
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
CATEGORIES = ("REGULAR", "SUPERNUMERARY", "NRI", "OCI", "FOREIGN_NATIONAL")
CARRYOVER_NOTE = "carryover from an earlier run on this database"


class ScenarioError(Exception):
    """An API call or precondition failed in a way the scenario cannot continue."""


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class StepResult:
    number: int
    title: str
    checks: list[Check] = field(default_factory=list)
    error: str | None = None
    ran: bool = True

    @property
    def ok(self) -> bool:
        return self.ran and self.error is None and all(c.ok for c in self.checks)


# ------------------------------------------------------------------ sample files


def load_manifest(path: Path = MANIFEST) -> dict[str, Any]:
    manifest: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return manifest


def read_csv_rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"), newline="")))


def build_xlsx(csv_bytes: bytes) -> bytes:
    """Generate the demo workbook from a strict-v1 CSV (all cells stay text)."""
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "admissions"
    sheet.append(list(HEADERS))
    for row in read_csv_rows(csv_bytes):
        sheet.append([row[name] for name in HEADERS])
    stream = io.BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def sample_bytes(manifest: dict[str, Any], name: str) -> bytes:
    entry = manifest["files"][name]
    source = entry.get("generated_from")
    if source is not None:
        return build_xlsx((SAMPLES / source).read_bytes())
    return (SAMPLES / name).read_bytes()


def raw_apaar_values(manifest: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for name in manifest["source_csv"]:
        for row in read_csv_rows((SAMPLES / name).read_bytes()):
            if row["apaar_id"]:
                values.add(row["apaar_id"])
    return values


def parse_report_csv(
    text: str,
) -> tuple[dict[str, str], dict[str, list[dict[str, str]]]]:
    """Report metadata ('# key' rows) and each titled table as dict rows."""
    metadata: dict[str, str] = {}
    tables: dict[str, list[dict[str, str]]] = {}
    rows = list(csv.reader(io.StringIO(text)))
    index = 0
    while index < len(rows):
        row = rows[index]
        index += 1
        if not row:
            continue
        if row[0].startswith("# ") and len(row) == 2:
            metadata[row[0][2:]] = row[1]
        elif row[0].startswith("# "):
            header = rows[index]
            index += 1
            body: list[dict[str, str]] = []
            while index < len(rows) and rows[index]:
                body.append(dict(zip(header, rows[index], strict=True)))
                index += 1
            tables[row[0][2:]] = body
    return metadata, tables


def finding_key(item: dict[str, Any]) -> tuple[Any, ...]:
    """Identity of a validation finding: what the manifest declares as truth."""
    evidence = item["evidence"]
    rows = evidence.get("source_row_numbers")
    if rows is None:
        rows = (
            [evidence["source_row_number"]] if "source_row_number" in evidence else []
        )
    discriminator = (
        evidence.get("category") or evidence.get("match_context") or item["field_name"]
    )
    return (
        item["rule_code"],
        discriminator or "",
        tuple(sorted(rows)),
        item["severity"],
        item["classification"],
    )


def expected_key(entry: dict[str, Any]) -> tuple[Any, ...]:
    return (
        entry["rule_code"],
        entry.get("discriminator", ""),
        tuple(sorted(entry.get("source_rows", []))),
        entry["severity"],
        entry["classification"],
    )


def ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 1.0


# ------------------------------------------------------------------ the scenario


class Scenario:
    """Thin API driver: each step calls public routes and records expectations."""

    def __init__(
        self,
        client: httpx2.Client,
        manifest: dict[str, Any] | None = None,
        *,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.client = client
        self.manifest = manifest or load_manifest()
        self.now = now
        self.tokens: dict[str, str] = {}
        self.steps: list[StepResult] = []
        self.step = StepResult(0, "setup")
        self.transcript: list[tuple[str, int, str]] = []
        self.batches: dict[str, str] = {}
        self.ctx: dict[str, Any] = {}
        self.fresh = True
        self.raw_apaar = raw_apaar_values(self.manifest)
        self.validation: dict[str, Any] = {
            "tp": 0,
            "fp": 0,
            "fn": 0,
            "carryover": 0,
            "evidence_checks": 0,
            "evidence_mismatches": 0,
            "per_file": {},
        }
        self.intake: dict[str, int] = {"checks": 0, "exact": 0}
        self.signals: dict[str, Any] = {"tp": 0, "fp": 0, "fn": 0, "carryover": 0}
        self.authorization: list[dict[str, Any]] = []
        self.reconciliation: list[dict[str, Any]] = []
        self.institutions = {
            slug: str(seed_id("institutions", slug))
            for slug in ("cedar", "maple", "willow")
        }
        self.programmes = {
            slug: str(seed_id("programmes", f"{slug}/{PROGRAMME}"))
            for slug in self.institutions
        }

    # ---------------------------------------------------------------- plumbing

    def headers(self, alias: str) -> dict[str, str]:
        if alias not in self.tokens:
            response = self.client.post(
                f"{API}/auth/demo-login", json={"demo_alias": alias}
            )
            if response.status_code == 404:
                raise ScenarioError(
                    "demo-login is unavailable: server is not in local DEMO_AUTH mode"
                )
            if response.status_code != 200:
                raise ScenarioError(
                    f"demo login failed for {alias} (HTTP {response.status_code}); "
                    "migrate and run `python -m app.seed` first"
                )
            self.tokens[alias] = response.json()["access_token"]
        return {"Authorization": f"Bearer {self.tokens[alias]}"}

    def request(
        self, alias: str, method: str, path: str, **kwargs: Any
    ) -> httpx2.Response:
        response = self.client.request(
            method, path, headers=self.headers(alias), **kwargs
        )
        self.transcript.append(
            (f"{method} {path.split('?')[0]}", response.status_code, response.text)
        )
        return response

    def call(
        self,
        alias: str,
        method: str,
        path: str,
        expect: int | tuple[int, ...] = 200,
        **kwargs: Any,
    ) -> httpx2.Response:
        response = self.request(alias, method, path, **kwargs)
        allowed = (expect,) if isinstance(expect, int) else expect
        if response.status_code not in allowed:
            code = ""
            try:
                code = str(response.json().get("error", {}).get("code", ""))
            except ValueError:
                pass
            hint = ""
            if code == "CREDENTIAL_SIGNING_UNAVAILABLE":
                hint = (
                    " (set CREDENTIAL_SIGNING_KEY on the server: "
                    'python -c "import base64,os;print(base64.b64encode(os.urandom(32))'
                    '.decode())")'
                )
            raise ScenarioError(
                f"{alias} {method} {path.split('?')[0]}: expected {allowed}, "
                f"got {response.status_code} {code}{hint}"
            )
        return response

    def get(self, alias: str, path: str, **params: Any) -> Any:
        return self.call(alias, "GET", path, params=params or None).json()

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.step.checks.append(Check(name, bool(ok), detail))

    def expect_eq(self, name: str, actual: object, expected: object) -> None:
        self.check(name, actual == expected, f"expected {expected!r}, got {actual!r}")

    def deny(
        self,
        name: str,
        alias: str,
        method: str,
        path: str,
        status: int,
        **kwargs: Any,
    ) -> None:
        response = self.request(alias, method, path, **kwargs)
        ok = response.status_code == status
        self.authorization.append(
            {
                "check": name,
                "expected": status,
                "actual": response.status_code,
                "ok": ok,
            }
        )
        self.check(
            f"authz: {name}", ok, f"expected {status}, got {response.status_code}"
        )

    # ---------------------------------------------------------------- building blocks

    def upload(self, alias: str, name: str) -> str:
        entry = self.manifest["files"][name]
        slug = entry["institution"]
        mime = XLSX_TYPE if name.endswith(".xlsx") else "text/csv"
        response = self.call(
            alias,
            "POST",
            f"{API}/submissions",
            expect=201,
            data={
                "institution_id": self.institutions[slug],
                "programme_id": self.programmes[slug],
                "academic_year": YEAR,
                "schema_version": "v1",
            },
            files={"file": (name, sample_bytes(self.manifest, name), mime)},
        )
        body = response.json()
        self.check(
            f"{name}: stored as unvalidated inactive candidate",
            body["validation_performed"] is False and body["status"] == "COMPLETED",
        )
        batch_id = str(body["id"])
        self.batches[name] = batch_id
        detail = self.get(alias, f"{API}/submissions/{batch_id}")
        self.expect_eq(f"{name}: row count", detail["row_count"], entry["rows"])
        self.check(f"{name}: not active after upload", detail["activated_at"] is None)
        return batch_id

    def validate(self, alias: str, name: str) -> dict[str, Any]:
        batch_id = self.batches[name]
        run: dict[str, Any] = self.call(
            alias, "POST", f"{API}/submissions/{batch_id}/validate", expect=201
        ).json()
        findings = self.all_findings(alias, batch_id, run["id"])
        self.score_validation(name, findings)
        return run

    def all_findings(
        self, alias: str, batch_id: str, run_id: str
    ) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        page = 1
        while True:
            body = self.get(
                alias,
                f"{API}/submissions/{batch_id}/findings",
                run_id=run_id,
                page=page,
                page_size=100,
            )
            found.extend(body["data"])
            if len(found) >= body["pagination"]["total"]:
                return found
            page += 1

    def score_validation(self, name: str, findings: list[dict[str, Any]]) -> None:
        entry = self.manifest["files"][name]
        expected = Counter(expected_key(e) for e in entry["findings"])
        produced = Counter(finding_key(f) for f in findings)
        tp = sum((expected & produced).values())
        fn = sum((expected - produced).values())
        extras = produced - expected
        # Earlier runs leave INFO-only history matches against the same peer values.
        carry = sum(
            n
            for key, n in extras.items()
            if not self.fresh
            and key[0] == "POTENTIAL_CROSS_INSTITUTION_DUPLICATE"
            and key[3] == "INFO"
        )
        fp = sum(extras.values()) - carry
        for item in entry["findings"]:
            wanted = item.get("evidence")
            if not wanted:
                continue
            key = expected_key(item)
            actual = next((f for f in findings if finding_key(f) == key), None)
            self.validation["evidence_checks"] += 1
            if actual is None or any(
                actual["evidence"].get(k) != v for k, v in wanted.items()
            ):
                self.validation["evidence_mismatches"] += 1
        stats = self.validation
        stats["tp"] += tp
        stats["fp"] += fp
        stats["fn"] += fn
        stats["carryover"] += carry
        stats["per_file"][name] = {
            "expected": sum(expected.values()),
            "produced": sum(produced.values()),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "carryover": carry,
        }
        self.check(
            f"{name}: findings match the manifest",
            fp == 0 and fn == 0,
            f"expected {sum(expected.values())}, produced {sum(produced.values())}, "
            f"TP {tp} FP {fp} FN {fn}"
            + (f", {carry} INFO {CARRYOVER_NOTE}" if carry else ""),
        )

    def review(self, alias: str, name: str, run_id: str) -> dict[str, Any]:
        batch_id = self.batches[name]
        review: dict[str, Any] = self.call(
            alias,
            "POST",
            f"{API}/submissions/{batch_id}/reviews",
            expect=201,
            json={"validation_run_id": run_id},
        ).json()
        return review

    def activate_request(self, review: dict[str, Any]) -> dict[str, Any]:
        return {
            "review_id": review["id"],
            "expected_scope_revision": review["expected_scope_revision"],
            "confirm_complete_replacement": True,
            "acknowledge_review_warnings": True,
            "acknowledge_omissions": True,
        }

    def activate(self, alias: str, name: str, run_id: str) -> dict[str, Any]:
        review = self.review(alias, name, run_id)
        result: dict[str, Any] = self.call(
            alias,
            "POST",
            f"{API}/submissions/{self.batches[name]}/activate",
            json=self.activate_request(review),
        ).json()
        return result

    def record_ids(self, alias: str, name: str) -> dict[str, str]:
        rows = self.get(
            alias,
            f"{API}/submissions/{self.batches[name]}/rows",
            page_size=100,
        )["data"]
        return {row["college_student_id"]: row["id"] for row in rows}

    def assess(self, alias: str, name: str) -> dict[str, Any]:
        body: dict[str, Any] = self.call(
            alias,
            "POST",
            f"{API}/submissions/{self.batches[name]}/intake-assessments",
            expect=201,
        ).json()
        self.score_intake(name, body["result"])
        return body

    def score_intake(self, name: str, result: dict[str, Any]) -> None:
        expected = self.manifest["files"][name]["intake"]
        lines = {line["category"]: line for line in result["categories"]}
        for category in CATEGORIES:
            want = expected["categories"].get(
                category, {"exceeded": False, "excess": 0}
            )
            for field_name, value in want.items():
                self.intake["checks"] += 1
                exact = lines[category].get(field_name) == value
                self.intake["exact"] += exact
                self.check(
                    f"{name}: intake {category}.{field_name}",
                    exact,
                    f"expected {value!r}, got {lines[category].get(field_name)!r}",
                )
        produced = Counter(
            (f["rule_id"], f.get("category", ""), f["calculation"])
            for f in result["findings"]
        )
        wanted = Counter(
            (f["rule_id"], f.get("category", ""), f["calculation"])
            for f in expected["findings"]
        )
        self.intake["checks"] += max(sum(wanted.values()), sum(produced.values()))
        self.intake["exact"] += sum((wanted & produced).values())
        self.check(
            f"{name}: intake engine findings and calculations exact",
            produced == wanted,
            f"expected {sorted(wanted)}, got {sorted(produced)}",
        )
        population = expected.get("missing_population")
        if population is not None:
            actual = result["missing_population"]
            for field_name, value in population.items():
                self.intake["checks"] += 1
                exact = actual.get(field_name) == value
                self.intake["exact"] += exact
                self.check(
                    f"{name}: missing population {field_name}",
                    exact,
                    f"expected {value!r}, got {actual.get(field_name)!r}",
                )

    def signal_ids(self, alias: str) -> dict[str, dict[str, Any]]:
        body = self.get(
            alias,
            f"{API}/integrity/institutions/{self.institutions['cedar']}/signals",
            academic_year=YEAR,
            programme_id=self.programmes["cedar"],
        )
        self.ctx["disclaimer"] = body["disclaimer"]
        return {s["rule_id"]: s for s in body["signals"]}

    def score_signals(self, label: str, produced: set[str], expected: set[str]) -> None:
        carry_rules = set(self.manifest["rerun_carryover"]["signals"])
        extra = produced - expected
        carry = extra & carry_rules if not self.fresh else set()
        tp, fn, fp = (
            len(produced & expected),
            len(expected - produced),
            len(extra - carry),
        )
        self.signals["tp"] += tp
        self.signals["fn"] += fn
        self.signals["fp"] += fp
        self.signals["carryover"] += len(carry)
        self.check(
            f"integrity signals {label} match the manifest",
            fp == 0 and fn == 0,
            f"expected {sorted(expected)}, got {sorted(produced)}",
        )

    # ---------------------------------------------------------------- the 12 steps

    def step_upload(self) -> None:
        for slug, admin in (
            ("cedar", "cedar_admin"),
            ("maple", "maple_admin"),
            ("willow", "willow_admin"),
        ):
            total = self.get(
                admin,
                f"{API}/submissions",
                institution_id=self.institutions[slug],
                academic_year=YEAR,
                page_size=1,
            )["pagination"]["total"]
            self.fresh = self.fresh and total == 0
        self.ctx["fresh"] = self.fresh
        policy = self.get("cedar_admin", f"{API}/submissions/upload-policy")
        self.expect_eq(
            "upload policy lists strict v1 headers",
            policy["required_headers"],
            list(HEADERS),
        )
        baseline = self.get(
            "demo_manager",
            f"{API}/analytics/case-performance",
            institution_id=self.institutions["cedar"],
        )
        self.ctx["case_baseline"] = baseline
        # Peer institutions are bootstrapped first so cedar's file can be compared
        # with their current ACTIVE snapshots.
        for admin, name in (
            ("maple_admin", "04_maple_peer.csv"),
            ("willow_admin", "08_willow_valid.xlsx"),
        ):
            self.upload(admin, name)
            run = self.validate(admin, name)
            result = self.activate(admin, name, run["id"])
            self.expect_eq(
                f"{name}: activated as current", result["scope_revision"] >= 1, True
            )
        for name in (
            "01_cedar_valid.csv",
            "02_cedar_apaar_issues.csv",
            "03_cedar_duplicates.csv",
            "05_cedar_intake_excess_and_peer_match.csv",
        ):
            self.upload("cedar_admin", name)

    def step_validate(self) -> None:
        runs = self.ctx.setdefault("runs", {})
        for name in (
            "01_cedar_valid.csv",
            "02_cedar_apaar_issues.csv",
            "03_cedar_duplicates.csv",
            "05_cedar_intake_excess_and_peer_match.csv",
        ):
            runs[name] = self.validate("cedar_admin", name)
        run = runs["02_cedar_apaar_issues.csv"]
        self.check(
            "run states local validation only",
            "not official APAAR verification" in run["validity_label"],
        )
        response = self.call(
            "cedar_admin",
            "GET",
            f"{API}/submissions/{self.batches['02_cedar_apaar_issues.csv']}/feedback.csv",
        )
        rows = read_csv_rows(response.content)
        self.check(
            "feedback.csv is a CSV attachment",
            response.headers["content-type"].startswith("text/csv")
            and "attachment" in response.headers["content-disposition"],
        )
        self.expect_eq(
            "feedback.csv row count",
            len(rows),
            self.manifest["files"]["02_cedar_apaar_issues.csv"]["feedback_rows"],
        )
        self.expect_eq(
            "feedback.csv rule codes",
            sorted(r["rule_code"] for r in rows if r["rule_code"]),
            sorted(
                e["rule_code"]
                for e in self.manifest["files"]["02_cedar_apaar_issues.csv"]["findings"]
            ),
        )
        self.check(
            "feedback.csv masks every APAAR",
            all("*" in r["apaar_id_masked"] or r["apaar_id_masked"] == "" for r in rows)
            and not any(
                raw in r["apaar_id_masked"] for r in rows for raw in self.raw_apaar
            ),
        )
        self.deny(
            "maple_admin cannot read cedar findings",
            "maple_admin",
            "GET",
            f"{API}/submissions/{self.batches['02_cedar_apaar_issues.csv']}/findings",
            404,
        )

    def step_activate(self) -> None:
        runs = self.ctx["runs"]
        name = "01_cedar_valid.csv"
        review = self.review("cedar_admin", name, runs[name]["id"])
        self.expect_eq("valid file review is READY", review["review_state"], "READY")
        result = self.call(
            "cedar_admin",
            "POST",
            f"{API}/submissions/{self.batches[name]}/activate",
            json=self.activate_request(review),
        ).json()
        self.check(
            "valid file activated as the cedar snapshot",
            (result["previous_batch_id"] is None) == self.fresh,
            f"previous snapshot {result['previous_batch_id']!r}",
        )
        blocked = "03_cedar_duplicates.csv"
        self.check(
            "blocked file lists a structural blocker",
            "DUPLICATE_COLLEGE_STUDENT_ID"
            in self.get("cedar_admin", f"{API}/submissions/{self.batches[blocked]}")[
                "activation_eligibility"
            ]["structural_blocking_rules"],
        )
        attempt = self.request(
            "cedar_admin",
            "POST",
            f"{API}/submissions/{self.batches[blocked]}/reviews",
            json={"validation_run_id": runs[blocked]["id"]},
        )
        self.expect_eq("blocked file review is BLOCKED", attempt.status_code, 201)
        activation = self.request(
            "cedar_admin",
            "POST",
            f"{API}/submissions/{self.batches[blocked]}/activate",
            json=self.activate_request(attempt.json()),
        )
        self.check(
            "duplicate college_student_id batch cannot be activated",
            attempt.json()["review_state"] == "BLOCKED"
            and activation.status_code == 409
            and activation.json()["error"]["code"] == "CANDIDATE_INELIGIBLE",
            f"review {attempt.json()['review_state']}, "
            f"activate HTTP {activation.status_code}",
        )
        declaration = self.call(
            "cedar_admin",
            "POST",
            f"{API}/institutions/{self.institutions['cedar']}/declarations",
            expect=201,
            json={
                "programme_id": self.programmes["cedar"],
                "academic_year": YEAR,
                "declared_total": self.manifest["declared_total"]["cedar"],
                "basis": "DEMO declaration for the Phase 10 scenario",
            },
        ).json()
        self.expect_eq(
            "declared total recorded",
            declaration["declared_total"],
            self.manifest["declared_total"]["cedar"],
        )

    def step_intake(self) -> None:
        name = "05_cedar_intake_excess_and_peer_match.csv"
        assessment = self.assess("demo_officer", name)
        self.check(
            "assessment carries DEMO label", assessment["source_label"] == "DEMO"
        )
        result = self.activate("cedar_admin", name, self.ctx["runs"][name]["id"])
        self.expect_eq(
            "over-limit candidate activated only with acknowledgement",
            result["previous_batch_id"],
            self.batches["01_cedar_valid.csv"],
        )
        missing = "06_cedar_missing_population.csv"
        self.upload("cedar_admin", missing)
        self.ctx["runs"][missing] = self.validate("cedar_admin", missing)
        self.assess("demo_officer", missing)

    def step_signals(self) -> None:
        signals = self.signal_ids("demo_officer")
        self.score_signals(
            "after intake review",
            set(signals),
            set(self.manifest["integrity_signals"]["before_cases"]),
        )
        exceeded = signals.get("CMP_INTAKE_EXCEEDED")
        self.check(
            "intake signal quotes the exact calculation",
            exceeded is not None
            and self.manifest["integrity_signals"]["intake_calculation"]
            in exceeded["calculation"],
        )
        self.check(
            "every signal links evidence",
            all(
                s["evidence"]["batch_ids"] or s["evidence"]["case_ids"]
                for s in signals.values()
            ),
        )
        self.check(
            "disclaimer states prompts are not fraud findings",
            "not fraud" in self.ctx["disclaimer"],
        )
        self.deny(
            "maple_admin cannot read cedar signals",
            "maple_admin",
            "GET",
            f"{API}/integrity/institutions/{self.institutions['cedar']}/signals",
            404,
        )

    def step_cases(self) -> None:
        main = "05_cedar_intake_excess_and_peer_match.csv"
        ids = self.record_ids("demo_officer", main)
        assignees = self.get("demo_officer", f"{API}/cases/assignees")
        officer_2 = next(
            a["id"] for a in assignees if a["display_name"] == "demo_officer_2"
        )
        case = self.call(
            "demo_officer",
            "POST",
            f"{API}/cases",
            expect=201,
            json={
                "category": "INTAKE_DISCREPANCY",
                "summary": "DEMO: REGULAR ACTIVE rows exceed the DEMO capacity",
                "record_version_ids": [ids["CED-004"]],
                "priority": "HIGH",
                "severity": "MEDIUM",
            },
        ).json()
        self.ctx["case_id"] = case["id"]
        assigned = self.call(
            "demo_officer",
            "POST",
            f"{API}/cases/{case['id']}/actions",
            expect=201,
            json={"action": "ASSIGNED", "assigned_to": officer_2},
        ).json()
        self.expect_eq(
            "case assigned to demo_officer_2", assigned["assigned_to"], officer_2
        )
        # The API accepts an explicit past due date, so no seeding helper is needed.
        overdue = self.call(
            "demo_officer",
            "POST",
            f"{API}/cases",
            expect=201,
            json={
                "category": "POTENTIAL_DUPLICATE",
                "summary": "DEMO: potential cross-institution match, transfer review",
                "record_version_ids": [ids["CED-005"]],
                "priority": "MEDIUM",
                "severity": "MEDIUM",
                "due_at": (self.now() - timedelta(days=10)).isoformat(),
            },
        ).json()
        self.ctx["overdue_case_id"] = overdue["id"]
        self.check(
            "case with explicit past due_at is overdue and escalated",
            overdue["is_overdue"] and overdue["is_escalated"],
        )
        self.call(
            "demo_officer_2",
            "POST",
            f"{API}/cases/{case['id']}/actions",
            expect=201,
            json={"action": "START_REVIEW"},
        )
        waiting = self.call(
            "demo_officer_2",
            "POST",
            f"{API}/cases/{case['id']}/actions",
            expect=201,
            json={
                "action": "REQUEST_CORRECTION",
                "comment": "Please review the REGULAR category assignments",
            },
        ).json()
        self.expect_eq("correction requested", waiting["status"], "AWAITING_CORRECTION")
        signals = self.signal_ids("demo_officer")
        overdue_signal = signals.get("CMP_OVERDUE_CASES")
        self.check(
            "overdue case raises a HIGH overdue-cases signal",
            overdue_signal is not None and overdue_signal["severity"] == "HIGH",
        )
        self.score_signals(
            "after overdue case",
            set(signals),
            set(self.manifest["integrity_signals"]["after_overdue_case"]),
        )
        self.deny(
            "demo_manager cannot list cases", "demo_manager", "GET", f"{API}/cases", 403
        )
        self.deny(
            "maple_admin cannot read cedar case",
            "maple_admin",
            "GET",
            f"{API}/cases/{case['id']}",
            404,
        )

    def step_correction(self) -> None:
        name = "07_cedar_corrected.csv"
        self.upload("cedar_admin", name)
        run = self.validate("cedar_admin", name)
        result = self.activate("cedar_admin", name, run["id"])
        self.expect_eq(
            "correction replaces the over-limit snapshot",
            result["previous_batch_id"],
            self.batches["05_cedar_intake_excess_and_peer_match.csv"],
        )
        self.assess("demo_officer", name)
        case = self.get("cedar_admin", f"{API}/cases/{self.ctx['case_id']}")
        self.expect_eq(
            "correction moved case to RESPONSE_SUBMITTED",
            case["status"],
            "RESPONSE_SUBMITTED",
        )
        self.check(
            "CORRECTION_RECEIVED event links the corrected batch",
            any(
                e["action"] == "CORRECTION_RECEIVED"
                and e["linked_batch_id"] == self.batches[name]
                for e in case["events"]
            ),
        )
        self.call(
            "cedar_admin",
            "POST",
            f"{API}/cases/{self.ctx['case_id']}/actions",
            expect=201,
            json={
                "action": "COMMENT",
                "comment": "DEMO: category for CED-004 corrected",
            },
        )

    def step_resolve(self) -> None:
        case_id = self.ctx["case_id"]
        url = f"{API}/cases/{case_id}/actions"
        self.deny(
            "cedar_admin cannot resolve a case",
            "cedar_admin",
            "POST",
            url,
            403,
            json={"action": "RESOLVED", "resolution_reason": "self-service"},
        )
        self.call(
            "demo_officer_2", "POST", url, expect=201, json={"action": "START_REVIEW"}
        )
        self.expect_eq(
            "resolving without a reason is rejected",
            self.request(
                "demo_officer_2", "POST", url, json={"action": "RESOLVED"}
            ).status_code,
            422,
        )
        self.expect_eq(
            "closing an unresolved case is rejected",
            self.request(
                "demo_officer_2", "POST", url, json={"action": "CLOSED"}
            ).status_code,
            409,
        )
        resolved = self.call(
            "demo_officer_2",
            "POST",
            url,
            expect=201,
            json={
                "action": "RESOLVED",
                "resolution_reason": "Corrected file removes the DEMO capacity excess",
            },
        ).json()
        self.expect_eq("case resolved", resolved["status"], "RESOLVED")
        closed = self.call(
            "demo_officer_2", "POST", url, expect=201, json={"action": "CLOSED"}
        ).json()
        self.expect_eq("case closed", closed["status"], "CLOSED")
        self.expect_eq(
            "resolution reason stored",
            closed["resolution_reason"],
            "Corrected file removes the DEMO capacity excess",
        )
        self.expect_eq(
            "case timeline is complete and ordered",
            [e["action"] for e in closed["events"]],
            self.manifest["case_timeline"],
        )
        self.check(
            "overdue case stays open for analytics",
            self.get("demo_officer", f"{API}/cases/{self.ctx['overdue_case_id']}")[
                "is_overdue"
            ],
        )

    def analytics(self, path: str, alias: str = "demo_manager", **params: Any) -> Any:
        return self.get(alias, f"{API}/analytics/{path}", **params)

    def step_analytics(self) -> None:
        expected = self.manifest["final_state"]
        for slug, want in expected.items():
            trends = self.analytics(
                "enrolment-trends",
                academic_year=YEAR,
                institution_id=self.institutions[slug],
                group_by="academic_year",
            )["data"][0]
            self.expect_eq(
                f"{slug}: declared records",
                trends["declared_records"],
                want["declared"],
            )
            self.expect_eq(
                f"{slug}: active records", trends["active_records"], want["active"]
            )
            self.expect_eq(
                f"{slug}: active by category",
                {
                    c: v["active_records"]
                    for c, v in trends["categories"].items()
                    if v["active_records"]
                },
                want["active_by_category"],
            )
        cedar = self.institutions["cedar"]
        rows = [
            r
            for r in self.analytics(
                "intake-utilisation", academic_year=YEAR, institution_id=cedar
            )["data"]
            if r["programme_code"] == PROGRAMME
        ]
        self.ctx["utilisation"] = rows
        for row in rows:
            want = expected["cedar"]["utilisation"][row["category"]]
            got = (
                row["approved_seats"],
                row["current_active"],
                row["exceeded"],
                row["excess"],
            )
            self.check(
                f"cedar {row['category']} utilisation", got == tuple(want), f"got {got}"
            )
        completeness = next(
            r
            for r in self.analytics(
                "submission-completeness", academic_year=YEAR, institution_id=cedar
            )["data"]
            if r["programme_code"] == PROGRAMME
        )
        self.check(
            "cedar completeness: declaration reconciles with snapshot",
            (
                completeness["declared_total"],
                completeness["current_declared_records"],
                completeness["shortfall"],
            )
            == (6, 6, 0),
        )
        self.check(
            "cedar completeness: pending candidates counted",
            completeness["pending_candidate_count"]
            >= expected["cedar"]["pending_candidates"],
        )
        performance = self.analytics("case-performance", institution_id=cedar)
        baseline = self.ctx["case_baseline"]["totals"]
        totals = performance["totals"]
        self.ctx["case_totals"] = totals
        for metric, delta in self.manifest["case_totals_delta"].items():
            self.expect_eq(
                f"case totals {metric} change", totals[metric] - baseline[metric], delta
            )
        self.check("analytics labelled DEMO", performance["source_label"] == "DEMO")
        self.deny(
            "verifier cannot read analytics",
            "demo_verifier",
            "GET",
            f"{API}/analytics/case-performance",
            403,
        )

    def step_credentials(self) -> None:
        ids = self.record_ids("cedar_admin", "07_cedar_corrected.csv")
        issued = self.call(
            "cedar_admin",
            "POST",
            f"{API}/credentials",
            expect=201,
            json={"record_version_id": ids["CED-001"]},
        ).json()
        token = issued["token"]
        self.expect_eq("credential is labelled DEMO", issued["source_label"], "DEMO")
        context = {"purpose": "ADMISSION_CHECK", "consent_ref": "consent-demo-phase10"}
        valid = self.call(
            "demo_verifier",
            "POST",
            f"{API}/credentials/verify",
            json={"token": token, **context},
        ).json()
        self.expect_eq("fresh credential verifies VALID", valid["outcome"], "VALID")
        self.check(
            "verifier sees only permitted claims",
            set(valid["claims"]) == set(self.manifest["permitted_claims"]),
        )
        middle = len(token.split(".")[1]) // 2
        payload = token.split(".")[1]
        swapped = "A" if payload[middle] != "A" else "B"
        tampered = ".".join(
            [
                token.split(".")[0],
                payload[:middle] + swapped + payload[middle + 1 :],
                token.split(".")[2],
            ]
        )
        bad = self.call(
            "demo_verifier",
            "POST",
            f"{API}/credentials/verify",
            json={"token": tampered, **context},
        ).json()
        self.expect_eq("tampered credential is INVALID", bad["outcome"], "INVALID")
        self.expect_eq("INVALID reveals no claims", bad["claims"], None)
        second = self.call(
            "demo_officer",
            "POST",
            f"{API}/credentials",
            expect=201,
            json={"record_version_id": ids["CED-002"]},
        ).json()
        self.call(
            "demo_officer",
            "POST",
            f"{API}/credentials/{second['credential']['id']}/revoke",
            json={"reason": "DEMO revocation for the scenario"},
        )
        revoked = self.call(
            "demo_verifier",
            "POST",
            f"{API}/credentials/verify",
            json={"token": second["token"], **context},
        ).json()
        self.expect_eq("revoked credential is REVOKED", revoked["outcome"], "REVOKED")
        self.expect_eq(
            "verification without consent is denied",
            self.request(
                "demo_verifier",
                "POST",
                f"{API}/credentials/verify",
                json={"token": token, "purpose": "ADMISSION_CHECK"},
            ).status_code,
            422,
        )
        log = self.get(
            "demo_verifier", f"{API}/credentials/verifications", page_size=100
        )
        outcomes = Counter(entry["outcome"] for entry in log["data"])
        self.check(
            "verification access log records all outcomes",
            all(outcomes[o] >= 1 for o in ("VALID", "INVALID", "REVOKED")),
            str(dict(outcomes)),
        )
        for name, path in (
            ("cases", f"{API}/cases"),
            ("records", f"{API}/records"),
            ("audit", f"{API}/audit/events"),
            ("submissions", f"{API}/submissions"),
        ):
            self.deny(f"verifier cannot read {name}", "demo_verifier", "GET", path, 403)

    def audit_count(self, action: str) -> list[dict[str, Any]]:
        body = self.get(
            "demo_officer",
            f"{API}/audit/events",
            action=action,
            institution_id=self.institutions["cedar"],
            page_size=100,
        )
        data: list[dict[str, Any]] = body["data"]
        return data

    def step_audit(self) -> None:
        actions = set(self.get("demo_officer", f"{API}/audit/actions")["data"])
        for action, actor in self.manifest["audit_expectations"].items():
            self.check(f"audit action {action} is listed", action in actions)
            events = self.audit_count(action)
            aliases = {(e["actor"] or {}).get("display_name", "SYSTEM") for e in events}
            self.check(
                f"audit {action} recorded by {actor}",
                actor in aliases,
                f"actors {sorted(aliases)}",
            )
        self.check(
            "audit details carry no APAAR or token fields",
            not any(
                key in str(self.audit_count("SUBMISSION_UPLOADED")).lower()
                for key in ("apaar", "token", "secret")
            ),
        )
        self.deny(
            "demo_manager cannot read audit",
            "demo_manager",
            "GET",
            f"{API}/audit/events",
            403,
        )
        self.deny(
            "cedar_admin cannot read audit",
            "cedar_admin",
            "GET",
            f"{API}/audit/events",
            403,
        )

    def export(
        self, kind: str, alias: str = "demo_officer", **params: Any
    ) -> tuple[dict[str, str], dict[str, list[dict[str, str]]]]:
        response = self.call(
            alias,
            "GET",
            f"{API}/reports/{kind}",
            params={"format": "csv", **params},
        )
        self.check(
            f"{kind}: CSV attachment",
            response.headers["content-type"].startswith("text/csv")
            and "attachment" in response.headers["content-disposition"],
        )
        meta, tables = parse_report_csv(response.text)
        self.check(
            f"{kind}: SIMULATED / DEMO provenance", meta["Provenance"].startswith(LABEL)
        )
        return meta, tables

    def reconcile(
        self, report: str, metric: str, report_value: object, analytics: object
    ) -> None:
        equal = report_value == analytics
        self.reconciliation.append(
            {
                "report": report,
                "metric": metric,
                "report_value": report_value,
                "analytics_value": analytics,
                "equal": equal,
            }
        )
        self.check(
            f"reconcile {report} {metric}",
            equal,
            f"report {report_value!r} vs analytics {analytics!r}",
        )

    def step_report(self) -> None:
        cedar = self.institutions["cedar"]
        filters = {"academic_year": YEAR, "institution_id": cedar}
        meta, tables = self.export("enrolment-summary", **filters)
        trends = self.analytics(
            "enrolment-trends",
            academic_year=YEAR,
            institution_id=cedar,
            group_by="academic_year",
        )["data"][0]
        totals = next(
            r for t, rows in tables.items() if t.startswith("Totals") for r in rows
        )
        self.reconcile(
            "enrolment-summary",
            "declared_records",
            int(totals["declared_records"]),
            trends["declared_records"],
        )
        self.reconcile(
            "enrolment-summary",
            "active_records",
            int(totals["active_records"]),
            trends["active_records"],
        )
        for category in ("REGULAR", "NRI", "SUPERNUMERARY"):
            self.reconcile(
                "enrolment-summary",
                f"active_{category}",
                int(totals[f"active_{category}"]),
                trends["categories"][category]["active_records"],
            )
        self.expect_eq(
            "report echoes the applied filters",
            meta["Filters applied"],
            f"academic_year={YEAR}; institution_id={cedar}",
        )
        _, tables = self.export("intake-utilisation", **filters)
        detail = [
            r
            for t, rows in tables.items()
            if t.startswith("Programme-year")
            for r in rows
            if r["programme_code"] == PROGRAMME
        ]
        by_category = {r["category"]: r for r in detail}
        for row in self.ctx["utilisation"]:
            mine = by_category[row["category"]]
            self.reconcile(
                "intake-utilisation",
                f"{row['category']}.current_active",
                int(mine["current_active"]),
                row["current_active"],
            )
            self.reconcile(
                "intake-utilisation",
                f"{row['category']}.approved_seats",
                int(mine["approved_seats"]),
                row["approved_seats"],
            )
        _, tables = self.export("open-cases", institution_id=cedar)
        totals = next(
            r
            for t, rows in tables.items()
            if t.startswith("Open case totals")
            for r in rows
        )
        analytics_totals = self.analytics("case-performance", institution_id=cedar)[
            "totals"
        ]
        for metric in ("open", "overdue", "escalated"):
            self.reconcile(
                "open-cases", metric, int(totals[metric]), analytics_totals[metric]
            )
        listed = [
            r for t, rows in tables.items() if t.startswith("Open cases") for r in rows
        ]
        overdue_rows = [
            r for r in listed if r["case_ref"] == self.ctx["overdue_case_id"][:8]
        ]
        self.check(
            "open-cases lists the overdue case and not the closed one",
            len(overdue_rows) == 1
            and overdue_rows[0]["overdue"] == "true"
            and not any(r["case_ref"] == self.ctx["case_id"][:8] for r in listed),
        )
        _, tables = self.export("resolution-times", institution_id=cedar)
        totals = next(
            r for t, rows in tables.items() if t.startswith("Case totals") for r in rows
        )
        self.reconcile(
            "resolution-times",
            "cases_total",
            int(totals["cases_total"]),
            analytics_totals["all"],
        )
        self.export("enrolment-summary", alias="demo_manager", **filters)
        exports = self.audit_count("REPORT_EXPORTED")
        self.check("report exports are audited", len(exports) >= 4)
        self.deny(
            "verifier cannot export reports",
            "demo_verifier",
            "GET",
            f"{API}/reports/enrolment-summary",
            403,
        )
        self.deny(
            "maple_admin cannot export another institution",
            "maple_admin",
            "GET",
            f"{API}/reports/enrolment-summary",
            404,
            params={"institution_id": cedar},
        )

    # ---------------------------------------------------------------- driver

    def run(self) -> bool:
        table: list[tuple[str, Callable[[], None]]] = [
            (
                "Institutions upload datasets (peers validated and activated first)",
                self.step_upload,
            ),
            (
                "Validate, and download the error report (feedback.csv)",
                self.step_validate,
            ),
            (
                "Review and activate valid data; invalid data stays blocked",
                self.step_activate,
            ),
            (
                "Intake engine flags the over-limit category and missing population",
                self.step_intake,
            ),
            (
                "Integrity signals explain the findings (review prompts, not fraud)",
                self.step_signals,
            ),
            (
                "Officer opens cases, assigns one to demo_officer_2, one overdue",
                self.step_cases,
            ),
            (
                "Institution submits the correction (new upload and activation)",
                self.step_correction,
            ),
            ("Reviewer resolves with a reason and closes the case", self.step_resolve),
            (
                "Analytics reflect the activated data and the case outcomes",
                self.step_analytics,
            ),
            (
                "Verifier checks VALID, tampered and revoked DEMO credentials",
                self.step_credentials,
            ),
            ("Audit explorer shows the key events and actors", self.step_audit),
            ("Filtered CSV reports reconcile with analytics", self.step_report),
        ]
        aborted = False
        for number, (title, action) in enumerate(table, start=1):
            self.step = StepResult(number, title, ran=not aborted)
            self.steps.append(self.step)
            if aborted:
                continue
            try:
                action()
            except ScenarioError as error:
                self.step.error = str(error)
                aborted = True
            except Exception as error:  # noqa: BLE001 - reported, never swallowed
                self.step.error = f"{type(error).__name__}: {error}"
                aborted = True
        return all(step.ok for step in self.steps) and not self.leaks()

    def leaks(self) -> list[str]:
        """Responses whose text contains a raw dataset APAAR value."""
        return sorted(
            {
                f"{label} -> {status}"
                for label, status, text in self.transcript
                if any(raw in text for raw in self.raw_apaar)
            }
        )

    def summary(self) -> dict[str, Any]:
        stats = self.validation
        tp, fp, fn = stats["tp"], stats["fp"], stats["fn"]
        sig = self.signals
        leaks = self.leaks()
        reconciled = sum(1 for r in self.reconciliation if r["equal"])
        authz_ok = sum(1 for a in self.authorization if a["ok"])
        completed = sum(1 for s in self.steps if s.ok)
        return {
            "scenario": "SIH26263 Phase 10 end-to-end demonstration",
            "source_label": LABEL,
            "fresh_database": self.fresh,
            "passed": completed == len(self.steps) and not leaks,
            "workflow": {"steps_passed": completed, "steps_total": len(self.steps)},
            "steps": [
                {
                    "number": s.number,
                    "title": s.title,
                    "status": "PASS" if s.ok else ("FAIL" if s.ran else "NOT_RUN"),
                    "checks_passed": sum(c.ok for c in s.checks),
                    "checks_total": len(s.checks),
                    "error": s.error,
                    "failed_checks": [
                        {"name": c.name, "detail": c.detail}
                        for c in s.checks
                        if not c.ok
                    ],
                }
                for s in self.steps
            ],
            "validation_accuracy": {
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "precision": ratio(tp, tp + fp),
                "recall": ratio(tp, tp + fn),
                "carryover_info_findings": stats["carryover"],
                "evidence_checks": stats["evidence_checks"],
                "evidence_mismatches": stats["evidence_mismatches"],
                "per_file": stats["per_file"],
            },
            "intake_correctness": {
                "checks": self.intake["checks"],
                "exact": self.intake["exact"],
                "exact_ratio": ratio(self.intake["exact"], self.intake["checks"]),
            },
            "integrity_signals": {
                "true_positives": sig["tp"],
                "false_positives": sig["fp"],
                "false_negatives": sig["fn"],
                "carryover": sig["carryover"],
            },
            "reconciliation": {
                "equal": reconciled,
                "total": len(self.reconciliation),
                "details": self.reconciliation,
            },
            "authorization": {
                "passed": authz_ok,
                "total": len(self.authorization),
                "details": self.authorization,
            },
            "raw_apaar_in_responses": {
                "responses_scanned": len(self.transcript),
                "raw_values_checked": len(self.raw_apaar),
                "leaks": leaks,
            },
        }


# ------------------------------------------------------------------ presentation


def render_table(summary: dict[str, Any]) -> str:
    state = "fresh" if summary["fresh_database"] else "previous run present"
    lines = [
        f"SIH26263 Phase 10 end-to-end demonstration  [{summary['source_label']}]",
        f"database state: {state}",
        "",
        f"{'#':>2}  {'RESULT':<7} {'CHECKS':>7}  STEP",
    ]
    for step in summary["steps"]:
        lines.append(
            f"{step['number']:>2}  {step['status']:<7} "
            f"{step['checks_passed']:>3}/{step['checks_total']:<3}  {step['title']}"
        )
        if step["error"]:
            lines.append(f"      ERROR: {step['error']}")
        lines.extend(
            f"      FAILED: {c['name']} ({c['detail']})" for c in step["failed_checks"]
        )
    v, i, s = (
        summary["validation_accuracy"],
        summary["intake_correctness"],
        summary["integrity_signals"],
    )
    w, r, a = summary["workflow"], summary["reconciliation"], summary["authorization"]
    leaks = summary["raw_apaar_in_responses"]
    carry = (
        f"  (+{v['carryover_info_findings']} INFO {CARRYOVER_NOTE})"
        if v["carryover_info_findings"]
        else ""
    )
    lines += [
        "",
        f"workflow            {w['steps_passed']}/{w['steps_total']} steps",
        f"validation          TP {v['true_positives']}  FP {v['false_positives']}  "
        f"FN {v['false_negatives']}  precision {v['precision']:.2f}  "
        f"recall {v['recall']:.2f}{carry}",
        f"intake correctness  {i['exact']}/{i['checks']} exact",
        f"integrity signals   TP {s['true_positives']}  FP {s['false_positives']}  "
        f"FN {s['false_negatives']}",
        f"reconciliation      {r['equal']}/{r['total']} equal",
        f"authorization       {a['passed']}/{a['total']} as expected",
        f"raw APAAR leaks     {len(leaks['leaks'])} in "
        f"{leaks['responses_scanned']} responses",
        f"RESULT              {'PASS' if summary['passed'] else 'FAIL'}",
    ]
    return "\n".join(lines)


def new_signing_key() -> str:
    return base64.b64encode(os.urandom(32)).decode()


LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
KEY_HELP = (
    "For --base-url the server needs a credential signing key, for example:\n"
    "  export CREDENTIAL_SIGNING_KEY=\"$(python -c 'import base64,os;"
    "print(base64.b64encode(os.urandom(32)).decode())')\"\n"
    "and APP_ENV=local DEMO_AUTH=true DEMO_AUTH_SECRET=<32+ bytes> "
    "APAAR_MATCHING_KEY=<32+ bytes>. The in-process mode generates an ephemeral key."
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.demo_scenario",
        description=__doc__.split("\n\n")[0] if __doc__ else None,
        epilog=KEY_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="print the JSON summary")
    parser.add_argument("--base-url", help="loopback server instead of in-process")
    parser.add_argument(
        "--write-xlsx",
        metavar="PATH",
        help="write the generated demo workbook and exit",
    )
    args = parser.parse_args(argv)
    manifest = load_manifest()
    if args.write_xlsx:
        source = next(
            e["generated_from"]
            for e in manifest["files"].values()
            if "generated_from" in e
        )
        Path(args.write_xlsx).write_bytes(build_xlsx((SAMPLES / source).read_bytes()))
        print(f"wrote {args.write_xlsx} ({LABEL})")
        return 0
    try:
        if args.base_url:
            host = urlsplit(args.base_url).hostname
            if host not in LOOPBACK_HOSTS:
                print(
                    "Refused: --base-url must be a loopback address.", file=sys.stderr
                )
                return 2
            return execute(
                httpx2.Client(base_url=args.base_url, timeout=60), manifest, args.json
            )
        settings = Settings()
        if settings.app_env != "local" or not settings.demo_auth:
            print("Refused: local DEMO_AUTH mode is required.", file=sys.stderr)
            return 2
        if settings.credential_signing_key is None:
            settings = Settings(credential_signing_key=SecretStr(new_signing_key()))
        from fastapi.testclient import TestClient

        from app.main import create_app

        with TestClient(
            create_app(settings),
            base_url="http://localhost",
            client=("127.0.0.1", 50000),
        ) as client:
            return execute(client, manifest, args.json)
    except (ValidationError, ScenarioError) as error:
        print(f"Demo scenario could not start: {error}", file=sys.stderr)
        return 2


def execute(client: httpx2.Client, manifest: dict[str, Any], as_json: bool) -> int:
    scenario = Scenario(client, manifest)
    scenario.run()
    summary = scenario.summary()
    print(json.dumps(summary, indent=2) if as_json else render_table(summary))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
