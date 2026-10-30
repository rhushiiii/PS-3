// Generated from FastAPI OpenAPI. Run npm run api:generate; do not edit.
export interface paths {
  "/api/v1/analytics/case-performance": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Case Performance */
    get: operations["case_performance_api_v1_analytics_case_performance_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/analytics/enrolment-trends": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Enrolment Trends */
    get: operations["enrolment_trends_api_v1_analytics_enrolment_trends_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/analytics/intake-utilisation": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Intake Utilisation */
    get: operations["intake_utilisation_api_v1_analytics_intake_utilisation_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/analytics/submission-completeness": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Submission Completeness */
    get: operations["submission_completeness_api_v1_analytics_submission_completeness_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/audit/actions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Actions */
    get: operations["actions_api_v1_audit_actions_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/audit/events": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Events */
    get: operations["events_api_v1_audit_events_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/audit/events/{event_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Event */
    get: operations["event_api_v1_audit_events__event_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/auth/demo-login": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Demo Login */
    post: operations["demo_login_api_v1_auth_demo_login_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/cases": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** List */
    get: operations["list__api_v1_cases_get"];
    put?: never;
    /** Create */
    post: operations["create_api_v1_cases_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/cases/assignees": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Assignees */
    get: operations["assignees_api_v1_cases_assignees_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/cases/{case_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Detail */
    get: operations["detail_api_v1_cases__case_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/cases/{case_id}/actions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Act */
    post: operations["act_api_v1_cases__case_id__actions_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/credentials": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * List Issued
     * @description List issued credentials in scope. Tokens are never returned here.
     */
    get: operations["list_issued_api_v1_credentials_get"];
    put?: never;
    /**
     * Issue
     * @description Issue a signed DEMO credential for an ACTIVE record in the current snapshot.
     *
     *     The token is returned once and never stored. Claims exclude APAAR and names.
     */
    post: operations["issue_api_v1_credentials_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/credentials/verifications": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Verifications
     * @description Verification access log: verifiers see their own, officers see all.
     */
    get: operations["verifications_api_v1_credentials_verifications_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/credentials/verify": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Verify
     * @description Verify a presented credential token (DEMO).
     *
     *     A QR code or scan is only a carrier for the token string; the Ed25519
     *     signature check is what establishes authenticity, never a database value
     *     alone. Purpose and consent_ref are mandatory (default deny). The token is
     *     not stored or logged. INVALID results reveal no claims.
     */
    post: operations["verify_api_v1_credentials_verify_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/credentials/{credential_id}/revoke": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Revoke */
    post: operations["revoke_api_v1_credentials__credential_id__revoke_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/health": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Health
     * @description Public liveness; deliberately independent of PostgreSQL.
     */
    get: operations["health_api_v1_health_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/institutions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Institutions */
    get: operations["institutions_api_v1_institutions_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/institutions/{institution_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Institution */
    get: operations["institution_api_v1_institutions__institution_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/institutions/{institution_id}/declarations": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Declarations */
    get: operations["declarations_api_v1_institutions__institution_id__declarations_get"];
    put?: never;
    /** Create Declaration */
    post: operations["create_declaration_api_v1_institutions__institution_id__declarations_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/institutions/{institution_id}/declarations/latest": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Latest */
    get: operations["latest_api_v1_institutions__institution_id__declarations_latest_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/institutions/{institution_id}/intake": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Intake */
    get: operations["intake_api_v1_institutions__institution_id__intake_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/institutions/{institution_id}/intake/changes": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Rule Changes */
    get: operations["rule_changes_api_v1_institutions__institution_id__intake_changes_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/institutions/{institution_id}/intake/simulate": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Simulate Intake */
    post: operations["simulate_intake_api_v1_institutions__institution_id__intake_simulate_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/institutions/{institution_id}/intake/{rule_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /** Patch Rule */
    patch: operations["patch_rule_api_v1_institutions__institution_id__intake__rule_id__patch"];
    trace?: never;
  };
  "/api/v1/institutions/{institution_id}/programmes": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Programmes */
    get: operations["programmes_api_v1_institutions__institution_id__programmes_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/institutions/{institution_id}/summary": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Summary */
    get: operations["summary_api_v1_institutions__institution_id__summary_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/integrity/institutions/{institution_id}/decisions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Decisions */
    get: operations["get_decisions_api_v1_integrity_institutions__institution_id__decisions_get"];
    put?: never;
    /** Post Decision */
    post: operations["post_decision_api_v1_integrity_institutions__institution_id__decisions_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/integrity/institutions/{institution_id}/signals": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Signals */
    get: operations["get_signals_api_v1_integrity_institutions__institution_id__signals_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/integrity/overview": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Overview */
    get: operations["get_overview_api_v1_integrity_overview_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Me */
    get: operations["me_api_v1_me_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/notifications": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** List */
    get: operations["list__api_v1_notifications_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/notifications/read-all": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Read All */
    post: operations["read_all_api_v1_notifications_read_all_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/notifications/unread-count": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Count */
    get: operations["count_api_v1_notifications_unread_count_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/notifications/{notification_id}/read": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Read */
    post: operations["read_api_v1_notifications__notification_id__read_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/ready": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Ready
     * @description Public database readiness; never expose connection errors or credentials.
     */
    get: operations["ready_api_v1_ready_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/records": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Registry */
    get: operations["registry_api_v1_records_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/records/{record_version_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Detail */
    get: operations["detail_api_v1_records__record_version_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/records/{record_version_id}/apaar-verify": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** History */
    get: operations["history_api_v1_records__record_version_id__apaar_verify_get"];
    put?: never;
    /**
     * Verify
     * @description Request a SIMULATED APAAR identity check (demo adapter only).
     *
     *     A valid local APAAR format is never identity confirmation. Provider
     *     unavailability, timeout or a pending result is never a mismatch.
     */
    post: operations["verify_api_v1_records__record_version_id__apaar_verify_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/reports/{kind}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Export Report */
    get: operations["export_report_api_v1_reports__kind__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** History */
    get: operations["history_api_v1_submissions_get"];
    put?: never;
    /**
     * Upload
     * @description Synthetic demo data only. Creates an unvalidated, inactive candidate snapshot from a CSV or XLSX file. An idempotent replay returns the original body with status 200 instead of 201.
     */
    post: operations["upload_api_v1_submissions_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/upload-policy": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Upload Policy */
    get: operations["upload_policy_api_v1_submissions_upload_policy_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/{batch_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Detail */
    get: operations["detail_api_v1_submissions__batch_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/{batch_id}/activate": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Activate Candidate */
    post: operations["activate_candidate_api_v1_submissions__batch_id__activate_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/{batch_id}/feedback.csv": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Feedback */
    get: operations["feedback_api_v1_submissions__batch_id__feedback_csv_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/{batch_id}/findings": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Findings */
    get: operations["findings_api_v1_submissions__batch_id__findings_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/{batch_id}/intake-assessments": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Assessments */
    get: operations["assessments_api_v1_submissions__batch_id__intake_assessments_get"];
    put?: never;
    /** Post Assessment */
    post: operations["post_assessment_api_v1_submissions__batch_id__intake_assessments_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/{batch_id}/intake-assessments/{assessment_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Assessment */
    get: operations["assessment_api_v1_submissions__batch_id__intake_assessments__assessment_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/{batch_id}/revalidate": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Revalidate */
    post: operations["revalidate_api_v1_submissions__batch_id__revalidate_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/{batch_id}/reviews": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Review Candidate */
    post: operations["review_candidate_api_v1_submissions__batch_id__reviews_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/{batch_id}/reviews/{review_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Review Detail */
    get: operations["review_detail_api_v1_submissions__batch_id__reviews__review_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/{batch_id}/rows": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Rows */
    get: operations["rows_api_v1_submissions__batch_id__rows_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/{batch_id}/validate": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Validate */
    post: operations["validate_api_v1_submissions__batch_id__validate_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/{batch_id}/validation-runs": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** History */
    get: operations["history_api_v1_submissions__batch_id__validation_runs_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/submissions/{batch_id}/validation-runs/{run_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Detail */
    get: operations["detail_api_v1_submissions__batch_id__validation_runs__run_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
}
export type webhooks = Record<string, never>;
export interface components {
  schemas: {
    /** ActivationRequest */
    ActivationRequest: {
      /**
       * Acknowledge Omissions
       * @default false
       */
      acknowledge_omissions: boolean;
      /**
       * Acknowledge Review Warnings
       * @constant
       */
      acknowledge_review_warnings: true;
      /**
       * Confirm Complete Replacement
       * @constant
       */
      confirm_complete_replacement: true;
      /** Expected Scope Revision */
      expected_scope_revision: number;
      /**
       * Review Id
       * Format: uuid
       */
      review_id: string;
    };
    /** ActivationResponse */
    ActivationResponse: {
      /**
       * Activated At
       * Format: date-time
       */
      activated_at: string;
      /**
       * Activated By
       * Format: uuid
       */
      activated_by: string;
      /**
       * Batch Id
       * Format: uuid
       */
      batch_id: string;
      /** Counts */
      counts: {
        [key: string]: unknown;
      };
      /** Previous Batch Id */
      previous_batch_id: string | null;
      /**
       * Review Id
       * Format: uuid
       */
      review_id: string;
      /**
       * Scope Id
       * Format: uuid
       */
      scope_id: string;
      /** Scope Revision */
      scope_revision: number;
      /**
       * Source Label
       * @default DEMO
       * @constant
       */
      source_label: "DEMO";
      /**
       * Validation Run Id
       * Format: uuid
       */
      validation_run_id: string;
    };
    /** Addition */
    Addition: {
      category: components["schemas"]["AdmissionCategory"];
      /** Count */
      count: number;
    };
    /**
     * AdmissionCategory
     * @enum {string}
     */
    AdmissionCategory:
      "REGULAR" | "SUPERNUMERARY" | "NRI" | "OCI" | "FOREIGN_NATIONAL";
    /** AgeBucket */
    AgeBucket: {
      /**
       * Bucket
       * @enum {string}
       */
      bucket: "0-7" | "8-14" | "15-30" | "31+";
      /** Count */
      count: number;
      /** Drilldown */
      drilldown: {
        [key: string]: string;
      };
      /** Max Days */
      max_days: number | null;
      /** Min Days */
      min_days: number;
    };
    /** AnalyticsFilters */
    AnalyticsFilters: {
      /** Academic Year */
      academic_year?: string | null;
      /** Group By */
      group_by?:
        ("academic_year" | "institution" | "programme" | "region") | null;
      /** Institution Id */
      institution_id?: string | null;
      /** Priority */
      priority?: ("LOW" | "MEDIUM" | "HIGH" | "URGENT") | null;
      /** Programme Code */
      programme_code?: string | null;
      /** Region */
      region?: string | null;
      /** Severity */
      severity?: ("LOW" | "MEDIUM" | "HIGH" | "CRITICAL") | null;
    };
    /** AssessmentResponse */
    AssessmentResponse: {
      /** Academic Year */
      academic_year: string;
      /**
       * Batch Id
       * Format: uuid
       */
      batch_id: string;
      /**
       * Computed At
       * Format: date-time
       */
      computed_at: string;
      /**
       * Computed By
       * Format: uuid
       */
      computed_by: string;
      /** Current Batch Id */
      current_batch_id: string | null;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
      /** Result */
      result: {
        [key: string]: unknown;
      };
      /** Rule Version */
      rule_version: string;
      /** Scope Revision */
      scope_revision: number;
      /**
       * Source Label
       * @default DEMO
       */
      source_label: string;
    };
    /** AssessmentSummary */
    AssessmentSummary: {
      /** Academic Year */
      academic_year: string;
      /**
       * Batch Id
       * Format: uuid
       */
      batch_id: string;
      /**
       * Computed At
       * Format: date-time
       */
      computed_at: string;
      /**
       * Computed By
       * Format: uuid
       */
      computed_by: string;
      /** Current Batch Id */
      current_batch_id: string | null;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
      /** Rule Version */
      rule_version: string;
      /** Scope Revision */
      scope_revision: number;
      /**
       * Source Label
       * @default DEMO
       */
      source_label: string;
    };
    /** AssigneeResponse */
    AssigneeResponse: {
      /** Display Name */
      display_name: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
    };
    /** AuditActionsResponse */
    AuditActionsResponse: {
      /** Data */
      data: string[];
    };
    /**
     * AuditActor
     * @description No email: only the role and demo alias identify who acted.
     */
    AuditActor: {
      /** Display Name */
      display_name: string;
      role: components["schemas"]["Role"] | null;
      /**
       * User Id
       * Format: uuid
       */
      user_id: string;
    };
    /** AuditEventResponse */
    AuditEventResponse: {
      /** Action */
      action: string;
      actor: components["schemas"]["AuditActor"] | null;
      /** Details */
      details: {
        [key: string]: unknown;
      };
      /**
       * Entity Id
       * Format: uuid
       */
      entity_id: string;
      /** Entity Type */
      entity_type: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Institution Id */
      institution_id: string | null;
      /**
       * Occurred At
       * Format: date-time
       */
      occurred_at: string;
    };
    /** BatchResponse */
    BatchResponse: {
      /** Academic Year */
      academic_year: string;
      /** Activated At */
      activated_at: string | null;
      /** Activation Eligibility */
      activation_eligibility?: {
        [key: string]: unknown;
      } | null;
      /** Activation Provenance */
      activation_provenance?: {
        [key: string]: unknown;
      } | null;
      /** Activation Review Id */
      activation_review_id: string | null;
      /** Base Batch Id */
      base_batch_id: string | null;
      /** Base Scope Revision */
      base_scope_revision: number;
      /** Completed At */
      completed_at: string | null;
      /** File Sha256 */
      file_sha256: string;
      /** File Size Bytes */
      file_size_bytes: number;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /**
       * Is Current
       * @default false
       */
      is_current: boolean;
      /** Latest Validation Run Id */
      latest_validation_run_id?: string | null;
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
      /**
       * Received At
       * Format: date-time
       */
      received_at: string;
      /** Row Count */
      row_count: number;
      /** Schema Version */
      schema_version: string;
      /**
       * Scope Id
       * Format: uuid
       */
      scope_id: string;
      /**
       * Snapshot State
       * @default CANDIDATE
       * @enum {string}
       */
      snapshot_state: "CANDIDATE" | "CURRENT" | "PREVIOUS";
      /** Source */
      source: string;
      status: components["schemas"]["ProcessingStatus"];
      /** Submission Mode */
      submission_mode: string;
      /**
       * Uploaded By
       * Format: uuid
       */
      uploaded_by: string;
      /**
       * Validation Performed
       * @default false
       */
      validation_performed: boolean;
      /** Validation Summary */
      validation_summary?: {
        [key: string]: unknown;
      } | null;
      /** Warnings */
      warnings?: string[];
    };
    /** CaseActionRequest */
    CaseActionRequest: {
      /**
       * Action
       * @enum {string}
       */
      action:
        | "COMMENT"
        | "ASSIGNED"
        | "START_REVIEW"
        | "REQUEST_CORRECTION"
        | "RESPONSE_SUBMITTED"
        | "UPDATED"
        | "RESOLVED"
        | "REJECTED"
        | "CLOSED";
      /** Assigned To */
      assigned_to?: string | null;
      /** Comment */
      comment?: string | null;
      /** Due At */
      due_at?: string | null;
      /** Priority */
      priority?: ("LOW" | "MEDIUM" | "HIGH" | "URGENT") | null;
      /** Resolution Reason */
      resolution_reason?: string | null;
      /** Severity */
      severity?: ("LOW" | "MEDIUM" | "HIGH" | "CRITICAL") | null;
    };
    /** CaseCreateRequest */
    CaseCreateRequest: {
      /**
       * Category
       * @enum {string}
       */
      category:
        | "POTENTIAL_DUPLICATE"
        | "APAAR_MISMATCH"
        | "INTAKE_DISCREPANCY"
        | "OTHER";
      /** Due At */
      due_at?: string | null;
      /**
       * Priority
       * @default MEDIUM
       * @enum {string}
       */
      priority: "LOW" | "MEDIUM" | "HIGH" | "URGENT";
      /** Record Version Ids */
      record_version_ids: string[];
      /**
       * Severity
       * @default MEDIUM
       * @enum {string}
       */
      severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
      /** Summary */
      summary: string;
    };
    /** CaseEventResponse */
    CaseEventResponse: {
      /**
       * Action
       * @enum {string}
       */
      action:
        | "OPENED"
        | "COMMENT"
        | "REQUEST_CORRECTION"
        | "CORRECTION_RECEIVED"
        | "ASSIGNED"
        | "START_REVIEW"
        | "RESPONSE_SUBMITTED"
        | "UPDATED"
        | "RESOLVED"
        | "REJECTED"
        | "CLOSED";
      /** Actor Id */
      actor_id: string | null;
      /**
       * Case Id
       * Format: uuid
       */
      case_id: string;
      /** Comment */
      comment: string | null;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Linked Batch Id */
      linked_batch_id: string | null;
    };
    /** CasePerformanceResponse */
    CasePerformanceResponse: {
      /** Ageing */
      ageing: components["schemas"]["AgeBucket"][];
      /**
       * As Of
       * Format: date-time
       */
      as_of: string;
      /** By Status */
      by_status: components["schemas"]["StatusCount"][];
      coverage: components["schemas"]["CoverageCounts"];
      /** Data */
      data: components["schemas"]["InstitutionCases"][];
      filters: components["schemas"]["AnalyticsFilters"];
      /**
       * Notice
       * @default DEMO data. Counts are declared rows in current activated snapshots, not verified enrolment. Missing data is unknown, never zero.
       */
      notice: string;
      /**
       * P90 Method
       * @default nearest-rank on elapsed days
       */
      p90_method: string;
      pagination: components["schemas"]["Pagination"];
      /** Resolution Days */
      resolution_days: components["schemas"]["ResolutionStats"][];
      /**
       * Source Label
       * @default DEMO
       * @constant
       */
      source_label: "DEMO";
      totals: components["schemas"]["CaseTotals"];
    };
    /** CaseResponse */
    CaseResponse: {
      /** Age Days */
      age_days: number;
      /** Assigned To */
      assigned_to: string | null;
      /**
       * Category
       * @enum {string}
       */
      category:
        | "POTENTIAL_DUPLICATE"
        | "APAAR_MISMATCH"
        | "INTAKE_DISCREPANCY"
        | "OTHER";
      /** Due At */
      due_at: string | null;
      /** Events */
      events: components["schemas"]["CaseEventResponse"][];
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /** Is Escalated */
      is_escalated: boolean;
      /** Is Overdue */
      is_overdue: boolean;
      /**
       * Opened At
       * Format: date-time
       */
      opened_at: string;
      /**
       * Opened By
       * Format: uuid
       */
      opened_by: string;
      /**
       * Priority
       * @enum {string}
       */
      priority: "LOW" | "MEDIUM" | "HIGH" | "URGENT";
      /** Record Version Ids */
      record_version_ids: string[];
      /** Resolution Reason */
      resolution_reason: string | null;
      /** Resolved At */
      resolved_at: string | null;
      /**
       * Severity
       * @enum {string}
       */
      severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
      /**
       * Status
       * @enum {string}
       */
      status:
        | "OPEN"
        | "ASSIGNED"
        | "UNDER_REVIEW"
        | "AWAITING_CORRECTION"
        | "RESPONSE_SUBMITTED"
        | "RESOLVED"
        | "REJECTED"
        | "CLOSED";
      /** Summary */
      summary: string;
    };
    /** CaseTotals */
    CaseTotals: {
      /** All */
      all: number;
      /** Escalated */
      escalated: number;
      /** Open */
      open: number;
      /** Overdue */
      overdue: number;
    };
    /** CategoryCount */
    CategoryCount: {
      /**
       * Active Records
       * @default 0
       */
      active_records: number;
      /**
       * Declared Records
       * @default 0
       */
      declared_records: number;
    };
    /** CompletenessResponse */
    CompletenessResponse: {
      /**
       * As Of
       * Format: date-time
       */
      as_of: string;
      coverage: components["schemas"]["CoverageCounts"];
      /** Data */
      data: components["schemas"]["CompletenessRow"][];
      filters: components["schemas"]["AnalyticsFilters"];
      /**
       * Notice
       * @default DEMO data. Counts are declared rows in current activated snapshots, not verified enrolment. Missing data is unknown, never zero.
       */
      notice: string;
      pagination: components["schemas"]["Pagination"];
      /** Rollups By Region */
      rollups_by_region: components["schemas"]["RegionRollup"][];
      /**
       * Source Label
       * @default DEMO
       * @constant
       */
      source_label: "DEMO";
      /** Stale After Days */
      stale_after_days: number;
    };
    /** CompletenessRow */
    CompletenessRow: {
      /** Academic Year */
      academic_year: string | null;
      /** Current Declared Records */
      current_declared_records: number | null;
      /** Declared Total */
      declared_total: number | null;
      /** Drilldown */
      drilldown: {
        [key: string]: string;
      };
      /** Freshness Days */
      freshness_days: number | null;
      /**
       * Freshness Status
       * @enum {string}
       */
      freshness_status: "FRESH" | "STALE" | "NO_CURRENT_SNAPSHOT";
      /** Has Current Snapshot */
      has_current_snapshot: boolean;
      /** Has Declaration */
      has_declaration: boolean;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /** Institution Name */
      institution_name: string;
      /** Last Activated At */
      last_activated_at: string | null;
      /** Pending Candidate Count */
      pending_candidate_count: number;
      /** Programme Code */
      programme_code: string;
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
      /** Region */
      region: string;
      /** Shortfall */
      shortfall: number | null;
      /** Stale */
      stale: boolean | null;
    };
    /** CoverageCounts */
    CoverageCounts: {
      /** Institutions Total */
      institutions_total: number;
      /** Institutions With Current Snapshot */
      institutions_with_current_snapshot: number;
      /** Programmes Total */
      programmes_total: number;
      /** Programmes With Current Snapshot */
      programmes_with_current_snapshot: number;
    };
    /** CredentialSummary */
    CredentialSummary: {
      /**
       * Expires At
       * Format: date-time
       */
      expires_at: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /**
       * Issued At
       * Format: date-time
       */
      issued_at: string;
      /**
       * Issued By
       * Format: uuid
       */
      issued_by: string;
      /** Kid */
      kid: string;
      /**
       * Record Version Id
       * Format: uuid
       */
      record_version_id: string;
      /**
       * Revoked
       * @default false
       */
      revoked: boolean;
      /** Revoked At */
      revoked_at?: string | null;
      /** Source Label */
      source_label: string;
    };
    /** CurrentUserResponse */
    CurrentUserResponse: {
      /**
       * Demo Mode
       * @default true
       */
      demo_mode: boolean;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Institution Id */
      institution_id: string | null;
      role: components["schemas"]["Role"];
    };
    /** DecisionRequest */
    DecisionRequest: {
      /**
       * Decision
       * @enum {string}
       */
      decision: "FALSE_POSITIVE" | "CONFIRMED_CONCERN" | "NEEDS_FOLLOW_UP";
      /** Reason */
      reason: string;
      /** Signal Key */
      signal_key: string;
    };
    /** DecisionResponse */
    DecisionResponse: {
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /**
       * Decided By
       * Format: uuid
       */
      decided_by: string;
      /**
       * Decision
       * @enum {string}
       */
      decision: "FALSE_POSITIVE" | "CONFIRMED_CONCERN" | "NEEDS_FOLLOW_UP";
      /**
       * Disclaimer
       * @default Rule-based review prompts computed from stored DEMO data. They are not fraud findings or compliance determinations, and are not official verification. Only AICTE officers decide; omission or missing data is never read as withdrawal or zero enrolment. Verification results are SIMULATED / DEMO DATA.
       */
      disclaimer: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /** Reason */
      reason: string;
      /** Signal Key */
      signal_key: string;
    };
    /** DeclarationRequest */
    DeclarationRequest: {
      /** Academic Year */
      academic_year: string;
      /** Basis */
      basis: string;
      /** Declared Total */
      declared_total: number;
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
    };
    /** DeclarationResponse */
    DeclarationResponse: {
      /** Academic Year */
      academic_year: string;
      /** Basis */
      basis: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /**
       * Declared By
       * Format: uuid
       */
      declared_by: string;
      /** Declared Total */
      declared_total: number;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
      /** Source Label */
      source_label: string;
    };
    /** DemoLogin */
    DemoLogin: {
      /** Demo Alias */
      demo_alias: string;
    };
    /** ErrorDetail */
    ErrorDetail: {
      /** Code */
      code: string;
      /** Message */
      message: string;
      /** Request Id */
      request_id: string;
    };
    /** ErrorResponse */
    ErrorResponse: {
      error: components["schemas"]["ErrorDetail"];
    };
    /** EvidenceRefs */
    EvidenceRefs: {
      /** Assessment Id */
      assessment_id?: string | null;
      /**
       * Batch Ids
       * @default []
       */
      batch_ids: string[];
      /**
       * Case Ids
       * @default []
       */
      case_ids: string[];
      /**
       * Finding Rule Counts
       * @default {}
       */
      finding_rule_counts: {
        [key: string]: number;
      };
      /**
       * Record Version Ids
       * @default []
       */
      record_version_ids: string[];
      /**
       * Record Version Total
       * @default 0
       */
      record_version_total: number;
      /** Validation Run Id */
      validation_run_id?: string | null;
    };
    /** FamilyScore */
    FamilyScore: {
      /** Active Count */
      active_count: number;
      /**
       * Family
       * @enum {string}
       */
      family: "DATA_QUALITY" | "IDENTITY_UNCERTAINTY" | "COMPLIANCE";
      /** Max Severity */
      max_severity: ("INFO" | "LOW" | "MEDIUM" | "HIGH") | null;
      /** Signal Count */
      signal_count: number;
      /** Weighted Points */
      weighted_points: number;
    };
    /** FieldChange */
    FieldChange: {
      /** Current */
      current: string | null;
      /** Field */
      field: string;
      /** Previous */
      previous: string | null;
    };
    /** FindingResponse */
    FindingResponse: {
      /**
       * Batch Id
       * Format: uuid
       */
      batch_id: string;
      /**
       * Classification
       * @enum {string}
       */
      classification: "ACTIVATION_BLOCKING" | "REVIEWABLE";
      /**
       * Cross Current Freshness
       * @enum {string}
       */
      cross_current_freshness: "FRESH" | "STALE";
      /**
       * Evaluated At
       * Format: date-time
       */
      evaluated_at: string;
      /** Evidence */
      evidence: {
        [key: string]: unknown;
      };
      /** Explanation */
      explanation: string;
      /** Field Name */
      field_name: string | null;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Ordinal */
      ordinal: number;
      /** Record Version Id */
      record_version_id: string | null;
      /** Rule Code */
      rule_code: string;
      /**
       * Run Id
       * Format: uuid
       */
      run_id: string;
      /**
       * Severity
       * @enum {string}
       */
      severity: "ERROR" | "WARNING" | "INFO";
    };
    /** FormatValidation */
    FormatValidation: {
      /**
       * Note
       * @default format check is local; not identity verification
       */
      note: string;
      /** Rule */
      rule: string;
      /** Valid */
      valid: boolean;
    };
    /** HistoryEntry */
    HistoryEntry: {
      /** Apaar Changed */
      apaar_changed: boolean | null;
      /**
       * Batch Id
       * Format: uuid
       */
      batch_id: string;
      /** Changes */
      changes: components["schemas"]["FieldChange"][];
      /**
       * Received At
       * Format: date-time
       */
      received_at: string;
      /**
       * Record Version Id
       * Format: uuid
       */
      record_version_id: string;
      /**
       * Snapshot State
       * @enum {string}
       */
      snapshot_state: "CURRENT" | "SUPERSEDED" | "CANDIDATE";
    };
    /** IdentityVerification */
    IdentityVerification: {
      /**
       * Completed At
       * Format: date-time
       */
      completed_at: string;
      /**
       * Provenance Label
       * @default SIMULATED — not an official government identity verification
       */
      provenance_label: string;
      /** Provider Request Id */
      provider_request_id: string | null;
      /**
       * Requested At
       * Format: date-time
       */
      requested_at: string;
      /**
       * Source Type
       * @default SIMULATED
       * @constant
       */
      source_type: "SIMULATED";
      /**
       * Status
       * @enum {string}
       */
      status:
        | "SIMULATED_MATCH"
        | "SIMULATED_MISMATCH"
        | "PENDING"
        | "SOURCE_UNAVAILABLE"
        | "SOURCE_TIMEOUT";
    };
    /** InstitutionCases */
    InstitutionCases: {
      /** Drilldown */
      drilldown: {
        [key: string]: string;
      };
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /** Institution Name */
      institution_name: string;
      /** Open */
      open: number;
      /** Overdue */
      overdue: number;
      /** Region */
      region: string;
      /** Resolved */
      resolved: number;
    };
    /** InstitutionResponse */
    InstitutionResponse: {
      /** Active */
      active: boolean;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** Permanent Id */
      permanent_id: string;
      /** Region */
      region: string;
    };
    /** InstitutionSummary */
    InstitutionSummary: {
      /** Academic Year */
      academic_year: string;
      /**
       * Count Basis
       * @default AVAILABLE_ACTIVATED_DECLARATIONS
       * @constant
       */
      count_basis: "AVAILABLE_ACTIVATED_DECLARATIONS";
      /** Coverage */
      coverage: {
        [key: string]: unknown;
      };
      /** Data */
      data: components["schemas"]["ProgrammeSummary"][];
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      pagination: components["schemas"]["Pagination"];
      /**
       * Source Label
       * @default DEMO
       * @constant
       */
      source_label: "DEMO";
      /** Totals */
      totals: {
        [key: string]: unknown;
      };
    };
    /** IntakeRuleResponse */
    IntakeRuleResponse: {
      /** Academic Year */
      academic_year: string;
      /** Approved Seats */
      approved_seats: number;
      category: components["schemas"]["AdmissionCategory"];
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
      /** Rule Version */
      rule_version: string;
      /** Source Label */
      source_label: string;
    };
    /** IssueRequest */
    IssueRequest: {
      /**
       * Record Version Id
       * Format: uuid
       */
      record_version_id: string;
    };
    /** IssueResponse */
    IssueResponse: {
      claims: components["schemas"]["PermittedClaims"];
      credential: components["schemas"]["CredentialSummary"];
      /**
       * Notice
       * @default The token is shown once and is not stored. DEMO credential signed by a prototype key; not an official AICTE, APAAR or government document
       */
      notice: string;
      /**
       * Source Label
       * @default DEMO
       */
      source_label: string;
      /** Token */
      token: string;
    };
    /** LivenessResponse */
    LivenessResponse: {
      /**
       * Status
       * @default ok
       * @constant
       */
      status: "ok";
    };
    /** NotificationResponse */
    NotificationResponse: {
      /** Body */
      body: string;
      /** Case Id */
      case_id: string | null;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Institution Id */
      institution_id: string | null;
      /**
       * Kind
       * @enum {string}
       */
      kind:
        | "CASE_ASSIGNED"
        | "CORRECTION_REQUESTED"
        | "RESPONSE_SUBMITTED"
        | "CASE_RESOLVED"
        | "CASE_REJECTED"
        | "CASE_CLOSED"
        | "CASE_OVERDUE";
      /** Read At */
      read_at: string | null;
      /** Title */
      title: string;
    };
    /** OmittedRecord */
    OmittedRecord: {
      /** College Student Id */
      college_student_id: string;
      /** Previous Admission Category */
      previous_admission_category: string;
      /** Previous Enrollment Status */
      previous_enrollment_status: string;
      /**
       * Record Version Id
       * Format: uuid
       */
      record_version_id: string;
      /** Source Row Number */
      source_row_number: number;
    };
    /** OverviewItem */
    OverviewItem: {
      /** Active Count */
      active_count: number;
      /** Dismissed Count */
      dismissed_count: number;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /** Institution Name */
      institution_name: string;
      score: components["schemas"]["ScoreSummary"];
      /** Signal Count */
      signal_count: number;
    };
    /** OverviewResponse */
    OverviewResponse: {
      /** Academic Year */
      academic_year: string | null;
      /** Band */
      band: ("LOW" | "MEDIUM" | "HIGH") | null;
      /** Data */
      data: components["schemas"]["OverviewItem"][];
      /**
       * Disclaimer
       * @default Rule-based review prompts computed from stored DEMO data. They are not fraud findings or compliance determinations, and are not official verification. Only AICTE officers decide; omission or missing data is never read as withdrawal or zero enrolment. Verification results are SIMULATED / DEMO DATA.
       */
      disclaimer: string;
      /**
       * Generated At
       * Format: date-time
       */
      generated_at: string;
      pagination: components["schemas"]["Pagination"];
      /**
       * Source Label
       * @default DEMO
       */
      source_label: string;
    };
    /** Page[AssessmentSummary] */
    Page_AssessmentSummary_: {
      /** Data */
      data: components["schemas"]["AssessmentSummary"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[AuditEventResponse] */
    Page_AuditEventResponse_: {
      /** Data */
      data: components["schemas"]["AuditEventResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[BatchResponse] */
    Page_BatchResponse_: {
      /** Data */
      data: components["schemas"]["BatchResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[CaseResponse] */
    Page_CaseResponse_: {
      /** Data */
      data: components["schemas"]["CaseResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[CredentialSummary] */
    Page_CredentialSummary_: {
      /** Data */
      data: components["schemas"]["CredentialSummary"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[DecisionResponse] */
    Page_DecisionResponse_: {
      /** Data */
      data: components["schemas"]["DecisionResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[DeclarationResponse] */
    Page_DeclarationResponse_: {
      /** Data */
      data: components["schemas"]["DeclarationResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[FindingResponse] */
    Page_FindingResponse_: {
      /** Data */
      data: components["schemas"]["FindingResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[InstitutionResponse] */
    Page_InstitutionResponse_: {
      /** Data */
      data: components["schemas"]["InstitutionResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[IntakeRuleResponse] */
    Page_IntakeRuleResponse_: {
      /** Data */
      data: components["schemas"]["IntakeRuleResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[NotificationResponse] */
    Page_NotificationResponse_: {
      /** Data */
      data: components["schemas"]["NotificationResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[ProgrammeResponse] */
    Page_ProgrammeResponse_: {
      /** Data */
      data: components["schemas"]["ProgrammeResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[RecordRow] */
    Page_RecordRow_: {
      /** Data */
      data: components["schemas"]["RecordRow"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[RowResponse] */
    Page_RowResponse_: {
      /** Data */
      data: components["schemas"]["RowResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[RuleChangeResponse] */
    Page_RuleChangeResponse_: {
      /** Data */
      data: components["schemas"]["RuleChangeResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[RunResponse] */
    Page_RunResponse_: {
      /** Data */
      data: components["schemas"]["RunResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[VerificationLogEntry] */
    Page_VerificationLogEntry_: {
      /** Data */
      data: components["schemas"]["VerificationLogEntry"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[VerificationResponse] */
    Page_VerificationResponse_: {
      /** Data */
      data: components["schemas"]["VerificationResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Pagination */
    Pagination: {
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
      /** Total */
      total: number;
    };
    /**
     * PermittedClaims
     * @description The only data a verifier may see. No APAAR, no student name.
     */
    PermittedClaims: {
      /** Academic Year */
      academic_year: string;
      /** Admission Category */
      admission_category: string;
      /** Enrollment Status */
      enrollment_status: string;
      /**
       * Expires At
       * Format: date-time
       */
      expires_at: string;
      /** Institution Name */
      institution_name: string;
      /**
       * Issued At
       * Format: date-time
       */
      issued_at: string;
      /** Programme Code */
      programme_code: string;
    };
    /**
     * ProcessingStatus
     * @enum {string}
     */
    ProcessingStatus: "RECEIVED" | "PROCESSING" | "COMPLETED" | "FAILED";
    /** ProgrammeResponse */
    ProgrammeResponse: {
      /** Active */
      active: boolean;
      /** Code */
      code: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /** Name */
      name: string;
    };
    /** ProgrammeSummary */
    ProgrammeSummary: {
      /** Counts */
      counts: {
        [key: string]: unknown;
      } | null;
      /** Has Current Snapshot */
      has_current_snapshot: boolean;
      /** Programme Code */
      programme_code: string;
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
    };
    /** Provenance */
    Provenance: {
      /** Activated At */
      activated_at: string | null;
      /**
       * Batch Id
       * Format: uuid
       */
      batch_id: string;
      /**
       * Received At
       * Format: date-time
       */
      received_at: string;
      /**
       * Snapshot State
       * @enum {string}
       */
      snapshot_state: "CURRENT" | "SUPERSEDED" | "CANDIDATE";
      /** Source */
      source: string;
      /** Superseded By Batch Id */
      superseded_by_batch_id: string | null;
    };
    /** ReadAllResponse */
    ReadAllResponse: {
      /** Marked Read */
      marked_read: number;
    };
    /** ReadinessResponse */
    ReadinessResponse: {
      /**
       * Database
       * @enum {string}
       */
      database: "reachable" | "unreachable";
      /**
       * Status
       * @enum {string}
       */
      status: "ready" | "unavailable";
    };
    /** RecordDetail */
    RecordDetail: {
      /** Academic Year */
      academic_year: string;
      /**
       * Batch Id
       * Format: uuid
       */
      batch_id: string;
      /** Cases */
      cases: components["schemas"]["RelatedCase"][];
      /** Category */
      category: string;
      /** College Student Id */
      college_student_id: string;
      /** Enrollment Date */
      enrollment_date: string | null;
      /** Enrollment Status */
      enrollment_status: string;
      /** Findings */
      findings: components["schemas"]["FindingResponse"][];
      /** History */
      history: components["schemas"]["HistoryEntry"][];
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /** Institution Name */
      institution_name: string;
      /** Is Current */
      is_current: boolean;
      /** Masked Apaar */
      masked_apaar: string;
      /** Presence Note */
      presence_note: string | null;
      /** Programme Code */
      programme_code: string;
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
      /** Programme Name */
      programme_name: string;
      provenance: components["schemas"]["Provenance"];
      /**
       * Record Version Id
       * Format: uuid
       */
      record_version_id: string;
      /**
       * Snapshot Presence
       * @enum {string}
       */
      snapshot_presence:
        "IN_LATEST_SNAPSHOT" | "NOT_IN_LATEST_SNAPSHOT" | "NOT_APPLICABLE";
      /**
       * Snapshot State
       * @enum {string}
       */
      snapshot_state: "CURRENT" | "SUPERSEDED" | "CANDIDATE";
      /**
       * Source Label
       * @default DEMO
       * @constant
       */
      source_label: "DEMO";
      /** Student Name */
      student_name: string;
      /** Validation Status */
      validation_status: ("VALID" | "FLAGGED" | "INCOMPLETE") | null;
      verification: components["schemas"]["VerificationSummary"] | null;
    };
    /** RecordRow */
    RecordRow: {
      /** Academic Year */
      academic_year: string;
      /**
       * Batch Id
       * Format: uuid
       */
      batch_id: string;
      /** Category */
      category: string;
      /** College Student Id */
      college_student_id: string;
      /** Enrollment Date */
      enrollment_date: string | null;
      /** Enrollment Status */
      enrollment_status: string;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /** Institution Name */
      institution_name: string;
      /** Is Current */
      is_current: boolean;
      /** Masked Apaar */
      masked_apaar: string;
      /** Programme Code */
      programme_code: string;
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
      /** Programme Name */
      programme_name: string;
      /**
       * Record Version Id
       * Format: uuid
       */
      record_version_id: string;
      /**
       * Snapshot State
       * @enum {string}
       */
      snapshot_state: "CURRENT" | "SUPERSEDED" | "CANDIDATE";
      /**
       * Source Label
       * @default DEMO
       * @constant
       */
      source_label: "DEMO";
      /** Student Name */
      student_name: string;
      /** Validation Status */
      validation_status: ("VALID" | "FLAGGED" | "INCOMPLETE") | null;
    };
    /** RegionRollup */
    RegionRollup: {
      /** Institutions Total */
      institutions_total: number;
      /** Pending Candidates */
      pending_candidates: number;
      /** Programme Years Total */
      programme_years_total: number;
      /** Region */
      region: string;
      /** Stale */
      stale: number;
      /** With Current Snapshot */
      with_current_snapshot: number;
      /** With Declaration */
      with_declaration: number;
      /** With Shortfall */
      with_shortfall: number;
    };
    /** RelatedCase */
    RelatedCase: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Is Overdue */
      is_overdue: boolean;
      /**
       * Opened At
       * Format: date-time
       */
      opened_at: string;
      /**
       * Priority
       * @enum {string}
       */
      priority: "LOW" | "MEDIUM" | "HIGH" | "URGENT";
      /**
       * Severity
       * @enum {string}
       */
      severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
      /**
       * Status
       * @enum {string}
       */
      status:
        | "OPEN"
        | "ASSIGNED"
        | "UNDER_REVIEW"
        | "AWAITING_CORRECTION"
        | "RESPONSE_SUBMITTED"
        | "RESOLVED"
        | "REJECTED"
        | "CLOSED";
    };
    /** ResolutionStats */
    ResolutionStats: {
      /** Mean Days */
      mean_days: number | null;
      /** Median Days */
      median_days: number | null;
      /** P90 Days */
      p90_days: number | null;
      /** Priority */
      priority: ("LOW" | "MEDIUM" | "HIGH" | "URGENT") | "ALL";
      /** Resolved Count */
      resolved_count: number;
    };
    /** ReviewRequest */
    ReviewRequest: {
      /**
       * Validation Run Id
       * Format: uuid
       */
      validation_run_id: string;
    };
    /** ReviewResponse */
    ReviewResponse: {
      /** Academic Year */
      academic_year: string;
      /** Assessment Now */
      assessment_now: {
        [key: string]: unknown;
      };
      /**
       * Batch Id
       * Format: uuid
       */
      batch_id: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Eligibility */
      eligibility: {
        [key: string]: unknown;
      };
      /** Expected Current Batch Id */
      expected_current_batch_id: string | null;
      /** Expected Scope Revision */
      expected_scope_revision: number;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /** Omission Pagination */
      omission_pagination: {
        [key: string]: number;
      } | null;
      /** Omitted Records */
      omitted_records: components["schemas"]["OmittedRecord"][] | null;
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
      /**
       * Receipt Label
       * @default Information presented for review; not proof it was read
       */
      receipt_label: string;
      /** Review Policy Version */
      review_policy_version: string;
      /**
       * Review State
       * @enum {string}
       */
      review_state: "READY" | "BLOCKED" | "STALE" | "CONSUMED";
      /**
       * Reviewed By
       * Format: uuid
       */
      reviewed_by: string;
      /**
       * Scope Id
       * Format: uuid
       */
      scope_id: string;
      /** Snapshot */
      snapshot: {
        [key: string]: unknown;
      };
      /**
       * Validation Run Id
       * Format: uuid
       */
      validation_run_id: string;
    };
    /** RevocationResponse */
    RevocationResponse: {
      /**
       * Credential Id
       * Format: uuid
       */
      credential_id: string;
      /**
       * Revoked At
       * Format: date-time
       */
      revoked_at: string;
      /**
       * Revoked By
       * Format: uuid
       */
      revoked_by: string;
    };
    /** RevokeRequest */
    RevokeRequest: {
      /** Reason */
      reason: string;
    };
    /**
     * Role
     * @enum {string}
     */
    Role:
      | "INSTITUTION_ADMIN"
      | "AICTE_OFFICER"
      | "AICTE_MANAGER"
      | "AUTHORIZED_VERIFIER";
    /** RowResponse */
    RowResponse: {
      /**
       * Abc Reconciliation Status
       * @default NOT_REQUESTED
       * @constant
       */
      abc_reconciliation_status: "NOT_REQUESTED";
      /** Academic Year */
      academic_year: string;
      /** Admission Category */
      admission_category: string;
      /** Apaar Id Masked */
      apaar_id_masked: string;
      /**
       * Apaar Verification Status
       * @default NOT_CHECKED
       * @constant
       */
      apaar_verification_status: "NOT_CHECKED";
      /**
       * Batch Id
       * Format: uuid
       */
      batch_id: string;
      /** College Student Id */
      college_student_id: string;
      /** Enrollment Date */
      enrollment_date: string | null;
      /** Enrollment Status */
      enrollment_status: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Programme Code */
      programme_code: string;
      /** Source Row Number */
      source_row_number: number;
      /** Student Name */
      student_name: string;
      /** Validation Run Id */
      validation_run_id?: string | null;
      /** Validation Status */
      validation_status?: ("VALID" | "FLAGGED" | "INCOMPLETE") | null;
    };
    /** RuleChangeRequest */
    RuleChangeRequest: {
      /** Approved Seats */
      approved_seats: number;
      /** Reason */
      reason: string;
    };
    /** RuleChangeResponse */
    RuleChangeResponse: {
      /**
       * Changed By
       * Format: uuid
       */
      changed_by: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Intake Rule Id
       * Format: uuid
       */
      intake_rule_id: string;
      /** New Approved Seats */
      new_approved_seats: number;
      /** New Rule Version */
      new_rule_version: string;
      /**
       * Notice
       * @default DEMO rule values for the prototype; not official AICTE policy. Rules-generated flags are not fraud determinations; officers decide.
       */
      notice: string;
      /** Old Approved Seats */
      old_approved_seats: number;
      /** Old Rule Version */
      old_rule_version: string;
      /** Reason */
      reason: string;
      /**
       * Source Label
       * @default DEMO
       */
      source_label: string;
    };
    /** RunResponse */
    RunResponse: {
      /**
       * Batch Id
       * Format: uuid
       */
      batch_id: string;
      /**
       * Completed At
       * Format: date-time
       */
      completed_at: string;
      /**
       * Cross Current Freshness
       * @enum {string}
       */
      cross_current_freshness: "FRESH" | "STALE";
      /** Current Overlap Records */
      current_overlap_records: number | null;
      /**
       * Evaluated At
       * Format: date-time
       */
      evaluated_at: string;
      /**
       * Historical Assessment
       * @default AS_OF_RUN
       * @constant
       */
      historical_assessment: "AS_OF_RUN";
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Kind
       * @enum {string}
       */
      kind: "INITIAL" | "REVALIDATION";
      /**
       * Requested By
       * Format: uuid
       */
      requested_by: string;
      /** Ruleset Snapshot */
      ruleset_snapshot: {
        [key: string]: unknown;
      };
      /** Ruleset Version */
      ruleset_version: string;
      /** Summary */
      summary: {
        [key: string]: unknown;
      };
      /**
       * Validity Label
       * @default Local validation only; not official APAAR verification
       */
      validity_label: string;
    };
    /** ScoreSummary */
    ScoreSummary: {
      /**
       * Band
       * @enum {string}
       */
      band: "LOW" | "MEDIUM" | "HIGH";
      /** Band Thresholds */
      band_thresholds: {
        [key: string]: number;
      };
      /** Components */
      components: components["schemas"]["FamilyScore"][];
      /**
       * Formula
       * @default sum over non-dismissed signals of severity weight
       */
      formula: string;
      /** Severity Weights */
      severity_weights: {
        [key: string]: number;
      };
      /** Total Points */
      total_points: number;
    };
    /** Signal */
    Signal: {
      /** Academic Year */
      academic_year?: string | null;
      /** Calculation */
      calculation: string;
      /** Decision */
      decision?:
        ("FALSE_POSITIVE" | "CONFIRMED_CONCERN" | "NEEDS_FOLLOW_UP") | null;
      /** Decision At */
      decision_at?: string | null;
      /**
       * Dismissed
       * @default false
       */
      dismissed: boolean;
      evidence: components["schemas"]["EvidenceRefs"];
      /**
       * Family
       * @enum {string}
       */
      family: "DATA_QUALITY" | "IDENTITY_UNCERTAINTY" | "COMPLIANCE";
      /** Programme Id */
      programme_id?: string | null;
      /** Recommended Next Action */
      recommended_next_action: string;
      /** Rule Id */
      rule_id: string;
      /**
       * Severity
       * @enum {string}
       */
      severity: "INFO" | "LOW" | "MEDIUM" | "HIGH";
      /** Signal Key */
      signal_key: string;
      /** Title */
      title: string;
    };
    /** SignalsResponse */
    SignalsResponse: {
      /** Academic Year */
      academic_year: string | null;
      /**
       * Disclaimer
       * @default Rule-based review prompts computed from stored DEMO data. They are not fraud findings or compliance determinations, and are not official verification. Only AICTE officers decide; omission or missing data is never read as withdrawal or zero enrolment. Verification results are SIMULATED / DEMO DATA.
       */
      disclaimer: string;
      /**
       * Generated At
       * Format: date-time
       */
      generated_at: string;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /** Parameters */
      parameters: {
        [key: string]: number;
      };
      /** Programme Id */
      programme_id: string | null;
      score: components["schemas"]["ScoreSummary"];
      /** Signals */
      signals: components["schemas"]["Signal"][];
      /**
       * Source Label
       * @default DEMO
       */
      source_label: string;
    };
    /** SimulationRequest */
    SimulationRequest: {
      /** Academic Year */
      academic_year: string;
      /** Additions */
      additions: components["schemas"]["Addition"][];
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
    };
    /** SimulationResponse */
    SimulationResponse: {
      /** Academic Year */
      academic_year: string;
      /** Categories */
      categories: {
        [key: string]: unknown;
      }[];
      /** Current Batch Id */
      current_batch_id: string | null;
      /** Has Current Snapshot */
      has_current_snapshot: boolean;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /**
       * Notice
       * @default DEMO rule values for the prototype; not official AICTE policy. Rules-generated flags are not fraud determinations; officers decide.
       */
      notice: string;
      /**
       * Persisted
       * @default false
       */
      persisted: boolean;
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
      /** Rule Version */
      rule_version: string;
      /**
       * Source Label
       * @default DEMO
       */
      source_label: string;
    };
    /** StatusCount */
    StatusCount: {
      /** Drilldown */
      drilldown: {
        [key: string]: string;
      };
      /** Escalated */
      escalated: number;
      /** Overdue */
      overdue: number;
      /**
       * Status
       * @enum {string}
       */
      status:
        | "OPEN"
        | "ASSIGNED"
        | "UNDER_REVIEW"
        | "AWAITING_CORRECTION"
        | "RESPONSE_SUBMITTED"
        | "RESOLVED"
        | "REJECTED"
        | "CLOSED";
      /** Total */
      total: number;
    };
    /** TokenResponse */
    TokenResponse: {
      /** Access Token */
      access_token: string;
      /**
       * Demo Mode
       * @default true
       * @constant
       */
      demo_mode: true;
      /** Expires In */
      expires_in: number;
      /**
       * Token Type
       * @default bearer
       * @constant
       */
      token_type: "bearer";
    };
    /** TrendRow */
    TrendRow: {
      /** Academic Year */
      academic_year: string;
      /** Active Records */
      active_records: number | null;
      /** Categories */
      categories: {
        [key: string]: components["schemas"]["CategoryCount"];
      } | null;
      /** Declared Records */
      declared_records: number | null;
      /** Drilldown */
      drilldown: {
        [key: string]: string;
      };
      /** Institution Id */
      institution_id?: string | null;
      /** Institution Name */
      institution_name?: string | null;
      /** Programme Code */
      programme_code?: string | null;
      /** Programme Id */
      programme_id?: string | null;
      /** Programmes Total */
      programmes_total: number;
      /** Programmes With Current Snapshot */
      programmes_with_current_snapshot: number;
      /** Region */
      region?: string | null;
      /**
       * Status
       * @enum {string}
       */
      status: "COMPLETE" | "PARTIAL" | "NO_CURRENT_SNAPSHOT";
      /** Unclassified Active Records */
      unclassified_active_records: number | null;
    };
    /** TrendsResponse */
    TrendsResponse: {
      /**
       * As Of
       * Format: date-time
       */
      as_of: string;
      coverage: components["schemas"]["CoverageCounts"];
      /** Data */
      data: components["schemas"]["TrendRow"][];
      filters: components["schemas"]["AnalyticsFilters"];
      /**
       * Group By
       * @enum {string}
       */
      group_by: "academic_year" | "institution" | "programme" | "region";
      /**
       * Notice
       * @default DEMO data. Counts are declared rows in current activated snapshots, not verified enrolment. Missing data is unknown, never zero.
       */
      notice: string;
      pagination: components["schemas"]["Pagination"];
      /**
       * Source Label
       * @default DEMO
       * @constant
       */
      source_label: "DEMO";
    };
    /** UnreadCountResponse */
    UnreadCountResponse: {
      /** Unread */
      unread: number;
    };
    /** UploadPolicyResponse */
    UploadPolicyResponse: {
      /**
       * Accepted Formats
       * @default [
       *       "csv",
       *       "xlsx"
       *     ]
       */
      accepted_formats: ("csv" | "xlsx")[];
      /**
       * Accepts Utf8 Bom
       * @default true
       * @constant
       */
      accepts_utf8_bom: true;
      /**
       * Encoding
       * @default UTF-8
       * @constant
       */
      encoding: "UTF-8";
      /** Max File Bytes */
      max_file_bytes: number;
      /** Max Rows */
      max_rows: number;
      /** Processing Timeout Seconds */
      processing_timeout_seconds: number;
      /** Receive Timeout Seconds */
      receive_timeout_seconds: number;
      /** Required Headers */
      required_headers: string[];
      /**
       * Schema Version
       * @default v1
       * @constant
       */
      schema_version: "v1";
    };
    /** UploadResponse */
    UploadResponse: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Status
       * @default COMPLETED
       * @constant
       */
      status: "COMPLETED";
      /**
       * Validation Performed
       * @default false
       * @constant
       */
      validation_performed: false;
      /** Warnings */
      warnings?: string[];
    };
    /** UtilisationResponse */
    UtilisationResponse: {
      /**
       * As Of
       * Format: date-time
       */
      as_of: string;
      coverage: components["schemas"]["CoverageCounts"];
      /** Data */
      data: components["schemas"]["UtilisationRow"][];
      filters: components["schemas"]["AnalyticsFilters"];
      /**
       * Notice
       * @default DEMO data. Counts are declared rows in current activated snapshots, not verified enrolment. Missing data is unknown, never zero.
       */
      notice: string;
      pagination: components["schemas"]["Pagination"];
      /** Pooling Note */
      pooling_note: string;
      /** Rule Version In Use */
      rule_version_in_use: string;
      /**
       * Source Label
       * @default DEMO
       * @constant
       */
      source_label: "DEMO";
    };
    /** UtilisationRow */
    UtilisationRow: {
      /** Academic Year */
      academic_year: string;
      /** Approved Seats */
      approved_seats: number | null;
      /** Calculation */
      calculation: string;
      /** Category */
      category: string;
      /** Current Active */
      current_active: number | null;
      /** Drilldown */
      drilldown: {
        [key: string]: string;
      };
      /** Exceeded */
      exceeded: boolean | null;
      /** Excess */
      excess: number | null;
      /**
       * Institution Id
       * Format: uuid
       */
      institution_id: string;
      /** Institution Name */
      institution_name: string;
      /** Programme Code */
      programme_code: string;
      /**
       * Programme Id
       * Format: uuid
       */
      programme_id: string;
      /** Remaining Capacity */
      remaining_capacity: number | null;
      /** Rule Version */
      rule_version: string | null;
      /**
       * Status
       * @enum {string}
       */
      status: "OK" | "NO_CURRENT_SNAPSHOT" | "NO_RULE";
      /** Utilisation Pct */
      utilisation_pct: number | null;
    };
    /** VerificationLogEntry */
    VerificationLogEntry: {
      /** Consent Ref */
      consent_ref: string;
      /** Credential Id */
      credential_id: string | null;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Outcome
       * @enum {string}
       */
      outcome: "VALID" | "INVALID" | "EXPIRED" | "REVOKED" | "UNAVAILABLE";
      /** Purpose */
      purpose: string;
      /**
       * Verified At
       * Format: date-time
       */
      verified_at: string;
      /**
       * Verifier User Id
       * Format: uuid
       */
      verifier_user_id: string;
    };
    /** VerificationRequest */
    VerificationRequest: {
      /** Consent Ref */
      consent_ref: string;
      /** Purpose */
      purpose: string;
      /** Retry Of */
      retry_of?: string | null;
    };
    /** VerificationResponse */
    VerificationResponse: {
      /** Adapter Type */
      adapter_type: string;
      /**
       * Batch Id
       * Format: uuid
       */
      batch_id: string;
      /**
       * Completed At
       * Format: date-time
       */
      completed_at: string;
      /** Evidence */
      evidence: {
        [key: string]: unknown;
      };
      /** External Reference */
      external_reference: string | null;
      format_validation: components["schemas"]["FormatValidation"];
      /**
       * Id
       * Format: uuid
       */
      id: string;
      identity_verification: components["schemas"]["IdentityVerification"];
      /**
       * Provenance Label
       * @default SIMULATED — not an official government identity verification
       */
      provenance_label: string;
      /** Provider Request Id */
      provider_request_id: string | null;
      /**
       * Record Version Id
       * Format: uuid
       */
      record_version_id: string;
      /**
       * Requested At
       * Format: date-time
       */
      requested_at: string;
      /**
       * Requested By
       * Format: uuid
       */
      requested_by: string;
      /** Retry Of Id */
      retry_of_id: string | null;
      /**
       * Status
       * @enum {string}
       */
      status:
        | "SIMULATED_MATCH"
        | "SIMULATED_MISMATCH"
        | "PENDING"
        | "SOURCE_UNAVAILABLE"
        | "SOURCE_TIMEOUT";
    };
    /** VerificationSummary */
    VerificationSummary: {
      /** Adapter Type */
      adapter_type: string;
      /**
       * Completed At
       * Format: date-time
       */
      completed_at: string;
      /** Provenance Label */
      provenance_label: string;
      /**
       * Requested At
       * Format: date-time
       */
      requested_at: string;
      /**
       * Source Type
       * @default SIMULATED
       * @constant
       */
      source_type: "SIMULATED";
      /**
       * Status
       * @enum {string}
       */
      status:
        | "SIMULATED_MATCH"
        | "SIMULATED_MISMATCH"
        | "PENDING"
        | "SOURCE_UNAVAILABLE"
        | "SOURCE_TIMEOUT";
    };
    /** VerifyRequest */
    VerifyRequest: {
      /** Consent Ref */
      consent_ref: string;
      /** Purpose */
      purpose: string;
      /** Token */
      token: string;
    };
    /** VerifyResponse */
    VerifyResponse: {
      claims: components["schemas"]["PermittedClaims"] | null;
      /**
       * Notice
       * @default DEMO credential signed by a prototype key; not an official AICTE, APAAR or government document
       */
      notice: string;
      /**
       * Outcome
       * @enum {string}
       */
      outcome: "VALID" | "INVALID" | "EXPIRED" | "REVOKED" | "UNAVAILABLE";
      /**
       * Source Label
       * @default DEMO
       */
      source_label: string;
      /**
       * Verification Id
       * Format: uuid
       */
      verification_id: string;
      /**
       * Verified At
       * Format: date-time
       */
      verified_at: string;
    };
  };
  responses: never;
  parameters: never;
  requestBodies: never;
  headers: never;
  pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
  case_performance_api_v1_analytics_case_performance_get: {
    parameters: {
      query?: {
        institution_id?: string | null;
        region?: string | null;
        priority?: ("LOW" | "MEDIUM" | "HIGH" | "URGENT") | null;
        severity?: ("LOW" | "MEDIUM" | "HIGH" | "CRITICAL") | null;
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CasePerformanceResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  enrolment_trends_api_v1_analytics_enrolment_trends_get: {
    parameters: {
      query?: {
        group_by?: "academic_year" | "institution" | "programme" | "region";
        page?: number;
        page_size?: number;
        academic_year?: string | null;
        institution_id?: string | null;
        region?: string | null;
        programme_code?: string | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["TrendsResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  intake_utilisation_api_v1_analytics_intake_utilisation_get: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
        academic_year?: string | null;
        institution_id?: string | null;
        region?: string | null;
        programme_code?: string | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["UtilisationResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  submission_completeness_api_v1_analytics_submission_completeness_get: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
        academic_year?: string | null;
        institution_id?: string | null;
        region?: string | null;
        programme_code?: string | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CompletenessResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  actions_api_v1_audit_actions_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AuditActionsResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  events_api_v1_audit_events_get: {
    parameters: {
      query?: {
        actor_user_id?: string | null;
        action?: string | null;
        entity_type?: string | null;
        institution_id?: string | null;
        from?: string | null;
        to?: string | null;
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_AuditEventResponse_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  event_api_v1_audit_events__event_id__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        event_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AuditEventResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  demo_login_api_v1_auth_demo_login_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["DemoLogin"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["TokenResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  list__api_v1_cases_get: {
    parameters: {
      query?: {
        institution_id?: string | null;
        status?:
          | (
              | "OPEN"
              | "ASSIGNED"
              | "UNDER_REVIEW"
              | "AWAITING_CORRECTION"
              | "RESPONSE_SUBMITTED"
              | "RESOLVED"
              | "REJECTED"
              | "CLOSED"
            )
          | null;
        severity?: ("LOW" | "MEDIUM" | "HIGH" | "CRITICAL") | null;
        priority?: ("LOW" | "MEDIUM" | "HIGH" | "URGENT") | null;
        programme_id?: string | null;
        assigned_to?: string | null;
        overdue?: boolean | null;
        min_age_days?: number | null;
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_CaseResponse_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  create_api_v1_cases_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CaseCreateRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CaseResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  assignees_api_v1_cases_assignees_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AssigneeResponse"][];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  detail_api_v1_cases__case_id__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        case_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CaseResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  act_api_v1_cases__case_id__actions_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        case_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CaseActionRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CaseResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  list_issued_api_v1_credentials_get: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_CredentialSummary_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  issue_api_v1_credentials_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["IssueRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["IssueResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  verifications_api_v1_credentials_verifications_get: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_VerificationLogEntry_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  verify_api_v1_credentials_verify_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["VerifyRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["VerifyResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  revoke_api_v1_credentials__credential_id__revoke_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        credential_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["RevokeRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RevocationResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  health_api_v1_health_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["LivenessResponse"];
        };
      };
    };
  };
  institutions_api_v1_institutions_get: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
        region?: string | null;
        q?: string | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_InstitutionResponse_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  institution_api_v1_institutions__institution_id__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        institution_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["InstitutionResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  declarations_api_v1_institutions__institution_id__declarations_get: {
    parameters: {
      query?: {
        programme_id?: string | null;
        academic_year?: string | null;
        page?: number;
        page_size?: number;
      };
      header?: never;
      path: {
        institution_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_DeclarationResponse_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  create_declaration_api_v1_institutions__institution_id__declarations_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        institution_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["DeclarationRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["DeclarationResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  latest_api_v1_institutions__institution_id__declarations_latest_get: {
    parameters: {
      query: {
        programme_id: string;
        academic_year: string;
      };
      header?: never;
      path: {
        institution_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["DeclarationResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  intake_api_v1_institutions__institution_id__intake_get: {
    parameters: {
      query: {
        academic_year: string;
        programme_id?: string | null;
        page?: number;
        page_size?: number;
      };
      header?: never;
      path: {
        institution_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_IntakeRuleResponse_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  rule_changes_api_v1_institutions__institution_id__intake_changes_get: {
    parameters: {
      query?: {
        intake_rule_id?: string | null;
        page?: number;
        page_size?: number;
      };
      header?: never;
      path: {
        institution_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_RuleChangeResponse_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  simulate_intake_api_v1_institutions__institution_id__intake_simulate_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        institution_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["SimulationRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SimulationResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  patch_rule_api_v1_institutions__institution_id__intake__rule_id__patch: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        institution_id: string;
        rule_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["RuleChangeRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RuleChangeResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  programmes_api_v1_institutions__institution_id__programmes_get: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
      };
      header?: never;
      path: {
        institution_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_ProgrammeResponse_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  summary_api_v1_institutions__institution_id__summary_get: {
    parameters: {
      query: {
        academic_year: string;
        programme_id?: string | null;
        page?: number;
        page_size?: number;
      };
      header?: never;
      path: {
        institution_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["InstitutionSummary"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  get_decisions_api_v1_integrity_institutions__institution_id__decisions_get: {
    parameters: {
      query?: {
        signal_key?: string | null;
        page?: number;
        page_size?: number;
      };
      header?: never;
      path: {
        institution_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_DecisionResponse_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  post_decision_api_v1_integrity_institutions__institution_id__decisions_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        institution_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["DecisionRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["DecisionResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  get_signals_api_v1_integrity_institutions__institution_id__signals_get: {
    parameters: {
      query?: {
        academic_year?: string | null;
        programme_id?: string | null;
      };
      header?: never;
      path: {
        institution_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SignalsResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  get_overview_api_v1_integrity_overview_get: {
    parameters: {
      query?: {
        academic_year?: string | null;
        band?: ("LOW" | "MEDIUM" | "HIGH") | null;
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OverviewResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  me_api_v1_me_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CurrentUserResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  list__api_v1_notifications_get: {
    parameters: {
      query?: {
        unread?: boolean;
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_NotificationResponse_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  read_all_api_v1_notifications_read_all_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ReadAllResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  count_api_v1_notifications_unread_count_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["UnreadCountResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  read_api_v1_notifications__notification_id__read_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        notification_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["NotificationResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  ready_api_v1_ready_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ReadinessResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ReadinessResponse"];
        };
      };
    };
  };
  registry_api_v1_records_get: {
    parameters: {
      query?: {
        institution_id?: string | null;
        programme_id?: string | null;
        academic_year?: string | null;
        enrollment_status?: string | null;
        validation_status?: ("VALID" | "FLAGGED" | "INCOMPLETE") | null;
        /** @description Case-insensitive college_student_id prefix or student name substring. APAAR values are never searchable. */
        q?: string | null;
        include_candidates?: boolean;
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_RecordRow_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  detail_api_v1_records__record_version_id__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        record_version_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RecordDetail"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  history_api_v1_records__record_version_id__apaar_verify_get: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
      };
      header?: never;
      path: {
        record_version_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_VerificationResponse_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Too Many Requests */
      429: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  verify_api_v1_records__record_version_id__apaar_verify_post: {
    parameters: {
      query?: never;
      header?: {
        /** @description Optional. Same key and body replays the original attempt. */
        "Idempotency-Key"?: string | null;
      };
      path: {
        record_version_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["VerificationRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["VerificationResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Too Many Requests */
      429: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  export_report_api_v1_reports__kind__get: {
    parameters: {
      query?: {
        format?: "csv" | "xlsx" | "pdf";
        academic_year?: string | null;
        institution_id?: string | null;
        region?: string | null;
        programme_code?: string | null;
        priority?: ("LOW" | "MEDIUM" | "HIGH" | "URGENT") | null;
        severity?: ("LOW" | "MEDIUM" | "HIGH" | "CRITICAL") | null;
      };
      header?: never;
      path: {
        kind:
          | "enrolment-summary"
          | "intake-utilisation"
          | "submission-completeness"
          | "resolution-times"
          | "validation-findings"
          | "open-cases"
          | "verification-activity";
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description The report file (aggregates only; DEMO provenance inside) */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/pdf": string;
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": string;
          "text/csv; charset=utf-8": string;
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Too Many Requests */
      429: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  history_api_v1_submissions_get: {
    parameters: {
      query?: {
        institution_id?: string | null;
        programme_id?: string | null;
        academic_year?: string | null;
        page?: number;
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_BatchResponse_"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Request Timeout */
      408: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Content Too Large */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  upload_api_v1_submissions_post: {
    parameters: {
      query?: never;
      header?: {
        /** @description Optional. Repeating a key with the same file and scope returns the original batch (HTTP 200, Idempotent-Replayed: true) without a new batch or audit event; the same key with different input is 409 IDEMPOTENCY_KEY_REUSED. Keys are scoped per institution. */
        "idempotency-key"?: string | null;
      };
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "multipart/form-data": {
          academic_year: string;
          /** Format: binary */
          file: string;
          /** Format: uuid */
          institution_id: string;
          /** Format: uuid */
          programme_id: string;
          /**
           * @default v1
           * @constant
           */
          schema_version?: "v1";
        };
      };
    };
    responses: {
      /** @description Idempotent replay */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["UploadResponse"];
        };
      };
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["UploadResponse"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Request Timeout */
      408: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Content Too Large */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  upload_policy_api_v1_submissions_upload_policy_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["UploadPolicyResponse"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Request Timeout */
      408: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Content Too Large */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  detail_api_v1_submissions__batch_id__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        batch_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["BatchResponse"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Request Timeout */
      408: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Content Too Large */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  activate_candidate_api_v1_submissions__batch_id__activate_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        batch_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ActivationRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ActivationResponse"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Request Timeout */
      408: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Content Too Large */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  feedback_api_v1_submissions__batch_id__feedback_csv_get: {
    parameters: {
      query?: {
        run_id?: string | null;
      };
      header?: never;
      path: {
        batch_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  findings_api_v1_submissions__batch_id__findings_get: {
    parameters: {
      query?: {
        run_id?: string | null;
        rule_code?: string | null;
        severity?: ("ERROR" | "WARNING" | "INFO") | null;
        classification?: ("ACTIVATION_BLOCKING" | "REVIEWABLE") | null;
        page?: number;
        page_size?: number;
      };
      header?: never;
      path: {
        batch_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_FindingResponse_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  assessments_api_v1_submissions__batch_id__intake_assessments_get: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
      };
      header?: never;
      path: {
        batch_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_AssessmentSummary_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  post_assessment_api_v1_submissions__batch_id__intake_assessments_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        batch_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AssessmentResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  assessment_api_v1_submissions__batch_id__intake_assessments__assessment_id__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        batch_id: string;
        assessment_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AssessmentResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  revalidate_api_v1_submissions__batch_id__revalidate_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        batch_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RunResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  review_candidate_api_v1_submissions__batch_id__reviews_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        batch_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ReviewRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ReviewResponse"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Request Timeout */
      408: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Content Too Large */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  review_detail_api_v1_submissions__batch_id__reviews__review_id__get: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
      };
      header?: never;
      path: {
        batch_id: string;
        review_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ReviewResponse"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Request Timeout */
      408: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Content Too Large */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  rows_api_v1_submissions__batch_id__rows_get: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
        run_id?: string | null;
        status?: ("VALID" | "FLAGGED" | "INCOMPLETE") | null;
      };
      header?: never;
      path: {
        batch_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_RowResponse_"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Request Timeout */
      408: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Content Too Large */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  validate_api_v1_submissions__batch_id__validate_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        batch_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RunResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  history_api_v1_submissions__batch_id__validation_runs_get: {
    parameters: {
      query?: {
        page?: number;
        page_size?: number;
      };
      header?: never;
      path: {
        batch_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_RunResponse_"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  detail_api_v1_submissions__batch_id__validation_runs__run_id__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        batch_id: string;
        run_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RunResponse"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
}
