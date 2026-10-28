// Generated from FastAPI OpenAPI. Run npm run api:generate; do not edit.
export interface paths {
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
    /** Verify */
    post: operations["verify_api_v1_records__record_version_id__apaar_verify_post"];
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
     * @description Synthetic demo data only. Creates an unvalidated, inactive candidate snapshot.
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
    /**
     * AdmissionCategory
     * @enum {string}
     */
    AdmissionCategory:
      "REGULAR" | "SUPERNUMERARY" | "NRI" | "OCI" | "FOREIGN_NATIONAL";
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
        "COMMENT" | "REQUEST_CORRECTION" | "ASSIGNED" | "RESOLVED" | "CLOSED";
      /** Assigned To */
      assigned_to?: string | null;
      /** Comment */
      comment?: string | null;
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
      /** Record Version Ids */
      record_version_ids: string[];
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
        | "RESOLVED"
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
    /** CaseResponse */
    CaseResponse: {
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
      /** Record Version Ids */
      record_version_ids: string[];
      /** Resolved At */
      resolved_at: string | null;
      /**
       * Status
       * @enum {string}
       */
      status:
        "OPEN" | "AWAITING_CORRECTION" | "UNDER_REVIEW" | "RESOLVED" | "CLOSED";
      /** Summary */
      summary: string;
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
    /** LivenessResponse */
    LivenessResponse: {
      /**
       * Status
       * @default ok
       * @constant
       */
      status: "ok";
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
    /** Page[ProgrammeResponse] */
    Page_ProgrammeResponse_: {
      /** Data */
      data: components["schemas"]["ProgrammeResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[RowResponse] */
    Page_RowResponse_: {
      /** Data */
      data: components["schemas"]["RowResponse"][];
      pagination: components["schemas"]["Pagination"];
    };
    /** Page[RunResponse] */
    Page_RunResponse_: {
      /** Data */
      data: components["schemas"]["RunResponse"][];
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
    /** UploadPolicyResponse */
    UploadPolicyResponse: {
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
    /** VerificationRequest */
    VerificationRequest: {
      /** Consent Ref */
      consent_ref: string;
      /** Purpose */
      purpose: string;
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
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Provenance Label
       * @default SIMULATED — not an official government identity verification
       */
      provenance_label: string;
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
      /**
       * Status
       * @enum {string}
       */
      status:
        | "SIMULATED_MATCH"
        | "SIMULATED_MISMATCH"
        | "PENDING"
        | "SOURCE_UNAVAILABLE";
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
        status?:
          | (
              | "OPEN"
              | "AWAITING_CORRECTION"
              | "UNDER_REVIEW"
              | "RESOLVED"
              | "CLOSED"
            )
          | null;
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
      header?: never;
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
      header?: never;
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
