"use client";

import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useSession, type Role } from "@/features/auth/session";
import { validAcademicYear } from "@/features/submissions/data";
import { CASE_PRIORITIES, CASE_SEVERITIES } from "@/features/cases/shared";
import {
  EnumSelect,
  InstitutionSelect,
  RegionSelect,
} from "@/components/ui/filters";
import { ApiError, errorMessage } from "@/lib/api/client";
import { saveBlob } from "@/lib/download";
import { DEMO_TAG, regionsOf } from "@/lib/format";
import {
  useInstitutionOptions,
  type InstitutionPage,
} from "@/features/institutions/options";

type Format = "csv" | "xlsx" | "pdf";
type Kind =
  | "enrolment-summary"
  | "intake-utilisation"
  | "submission-completeness"
  | "resolution-times"
  | "validation-findings"
  | "open-cases"
  | "verification-activity";
type Filters = {
  year: string;
  institution: string;
  region: string;
  programme: string;
  priority: string;
  severity: string;
};

const FORMATS: Record<Format, { label: string; accept: string }> = {
  csv: { label: "CSV", accept: "text/csv" },
  xlsx: {
    label: "Excel (.xlsx)",
    accept: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  },
  pdf: { label: "PDF", accept: "application/pdf" },
};

const REPORTS: {
  kind: Kind;
  title: string;
  description: string;
  roles: Role[];
  cases?: boolean;
}[] = [
  {
    kind: "enrolment-summary",
    title: "Enrolment summary",
    description: "Aggregate enrolment by academic year, programme and region.",
    roles: ["INSTITUTION_ADMIN", "AICTE_OFFICER", "AICTE_MANAGER"],
  },
  {
    kind: "intake-utilisation",
    title: "Intake utilisation",
    description:
      "Declared enrolment against approved capacity per seat category.",
    roles: ["INSTITUTION_ADMIN", "AICTE_OFFICER", "AICTE_MANAGER"],
  },
  {
    kind: "submission-completeness",
    title: "Submission completeness",
    description: "Which programmes have a current activated snapshot.",
    roles: ["INSTITUTION_ADMIN", "AICTE_OFFICER", "AICTE_MANAGER"],
  },
  {
    kind: "resolution-times",
    title: "Resolution times",
    description: "How long cases take to resolve, by priority.",
    roles: ["INSTITUTION_ADMIN", "AICTE_OFFICER", "AICTE_MANAGER"],
    cases: true,
  },
  {
    kind: "validation-findings",
    title: "Validation findings",
    description: "Counts of validation findings by rule and severity.",
    roles: ["INSTITUTION_ADMIN", "AICTE_OFFICER", "AICTE_MANAGER"],
    cases: true,
  },
  {
    kind: "open-cases",
    title: "Open cases",
    description: "Cases that are still open, with priority and age.",
    roles: ["INSTITUTION_ADMIN", "AICTE_OFFICER"],
    cases: true,
  },
  {
    kind: "verification-activity",
    title: "Verification activity",
    description: "Summary of recorded verification requests and outcomes.",
    roles: ["AICTE_OFFICER"],
  },
];

const EMPTY: Filters = {
  year: "",
  institution: "",
  region: "",
  programme: "",
  priority: "",
  severity: "",
};

function ReportCard({
  report,
  institutions,
  regions,
  fixedInstitution,
  initial,
}: {
  report: (typeof REPORTS)[number];
  institutions: InstitutionPage["data"];
  regions: string[];
  fixedInstitution: boolean;
  initial: Filters;
}) {
  const { download } = useSession();
  const [filters, setFilters] = useState<Filters>(initial);
  const [format, setFormat] = useState<Format>("csv");
  const [validation, setValidation] = useState("");
  const [status, setStatus] = useState("");
  const id = `report-${report.kind}`;
  const set = (key: keyof Filters, value: string) =>
    setFilters((f) => ({ ...f, [key]: value }));

  const exportReport = useMutation({
    mutationFn: () => {
      const query = new URLSearchParams({ format });
      if (filters.year) query.set("academic_year", filters.year);
      if (!fixedInstitution && filters.institution)
        query.set("institution_id", filters.institution);
      if (filters.region) query.set("region", filters.region);
      if (filters.programme.trim())
        query.set("programme_code", filters.programme.trim());
      if (report.cases) {
        if (filters.priority) query.set("priority", filters.priority);
        if (filters.severity) query.set("severity", filters.severity);
      }
      return download(`/reports/${report.kind}?${query}`, undefined, {
        accept: FORMATS[format].accept,
        fallbackName: `${report.kind}.${format}`,
      });
    },
    retry: false,
    onMutate: () => setStatus(""),
    onSuccess: ({ blob, filename }) => {
      saveBlob({ blob, filename });
      setStatus(`Report downloaded: ${filename}`);
    },
  });

  function submit() {
    if (filters.year && !validAcademicYear(filters.year)) {
      setValidation("Enter a consecutive academic year, for example 2026-27.");
      return;
    }
    setValidation("");
    exportReport.mutate();
  }

  return (
    <section className="panel dashboard-panel" aria-labelledby={`${id}-title`}>
      <h2 id={`${id}-title`}>{report.title}</h2>
      <p>{report.description}</p>
      <form
        className="dashboard-filters"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <label>
          Academic year
          <input
            value={filters.year}
            onChange={(e) => set("year", e.target.value)}
            placeholder="All years, or 2026-27"
          />
        </label>
        {!fixedInstitution && (
          <InstitutionSelect
            institutions={institutions}
            value={filters.institution}
            onChange={(value) => set("institution", value)}
          />
        )}
        <RegionSelect
          regions={regions}
          value={filters.region}
          onChange={(value) => set("region", value)}
        />
        <label>
          Programme code
          <input
            value={filters.programme}
            maxLength={40}
            onChange={(e) => set("programme", e.target.value)}
            placeholder="Optional"
          />
        </label>
        {report.cases && (
          <>
            <EnumSelect
              label="Priority"
              values={CASE_PRIORITIES}
              value={filters.priority}
              onChange={(value) => set("priority", value)}
              allLabel="Any priority"
            />
            <EnumSelect
              label="Severity"
              values={CASE_SEVERITIES}
              value={filters.severity}
              onChange={(value) => set("severity", value)}
              allLabel="Any severity"
            />
          </>
        )}
        <label>
          Format
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value as Format)}
          >
            {(Object.keys(FORMATS) as Format[]).map((f) => (
              <option key={f} value={f}>
                {FORMATS[f].label}
              </option>
            ))}
          </select>
        </label>
        <button
          className="button"
          type="submit"
          disabled={exportReport.isPending}
          aria-describedby={`${id}-status`}
        >
          {exportReport.isPending ? "Preparing…" : "Download report"}
        </button>
      </form>
      {validation && (
        <p className="form-error" role="alert">
          {validation}
        </p>
      )}
      {exportReport.isError && (
        <p className="form-error" role="alert">
          {errorMessage(exportReport.error)}
          {exportReport.error instanceof ApiError &&
            exportReport.error.requestId &&
            ` Request reference: ${exportReport.error.requestId}`}
        </p>
      )}
      <p id={`${id}-status`} aria-live="polite" className="data-note">
        {exportReport.isPending ? "Preparing report…" : status}
      </p>
    </section>
  );
}

export function ReportCenter() {
  const { session } = useSession();
  const search = useSearchParams();
  const role = session?.user.role;
  const fixedInstitution = role === "INSTITUTION_ADMIN";
  const institutions = useInstitutionOptions(!!session && !fixedInstitution);
  if (!role) return null;
  const list = institutions.data?.data ?? [];
  const regions = regionsOf(list);
  const year = search.get("academic_year") ?? "";
  const institution = search.get("institution_id") ?? "";
  const initial: Filters = {
    ...EMPTY,
    year: validAcademicYear(year) ? year : "",
    institution: list.some((i) => i.id === institution) ? institution : "",
    region: regions.includes(search.get("region") ?? "")
      ? (search.get("region") ?? "")
      : "",
  };
  const available = REPORTS.filter((r) => r.roles.includes(role));

  return (
    <div className="dashboard-page">
      <header className="page-heading">
        <p className="eyebrow">REPORTS</p>
        <h1>Reports</h1>
        <p>
          Download aggregate reports as CSV, Excel or PDF. Report totals
          reconcile with the analytics views for the same filters. Every report
          is labelled <strong>{DEMO_TAG}</strong>: all records are
          synthetic.
          {fixedInstitution && " Reports are limited to your institution."}
        </p>
      </header>
      {institutions.isError && (
        <p className="form-error" role="alert">
          Institution and region options could not be loaded.
        </p>
      )}
      {available.map((report) => (
        <ReportCard
          // Remount once options load so query-param prefill can apply.
          key={`${report.kind}-${list.length}`}
          report={report}
          institutions={list}
          regions={regions}
          fixedInstitution={fixedInstitution}
          initial={initial}
        />
      ))}
    </div>
  );
}
