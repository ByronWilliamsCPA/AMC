/**
 * Thin, readable wrappers over the generated SDK.
 *
 * The generated function names encode the full path (e.g.
 * `submitExamApiV1ExamsExamIdAttemptsPost`); these aliases give feature code a
 * clean surface and unwrap the `{ data, error }` envelope into a value or a
 * thrown {@link ApiError}, so callers (and TanStack Query) get normal
 * promise semantics.
 */
import {
  createInviteApiV1InvitesPost,
  getDiagnosticApiV1DiagnosticsInstrumentIdGet,
  getExamApiV1ExamsExamIdGet,
  getMyProgressApiV1ProgressGet,
  getUserProgressApiV1UsersUserIdProgressGet,
  listDiagnosticsApiV1DiagnosticsGet,
  listExamsApiV1ExamsGet,
  loginApiV1AuthLoginPost,
  logoutApiV1AuthLogoutPost,
  meApiV1AuthMeGet,
  registerApiV1AuthRegisterPost,
  submitDiagnosticApiV1DiagnosticsInstrumentIdAttemptsPost,
  submitExamApiV1ExamsExamIdAttemptsPost,
  validateInviteApiV1AuthInvitesTokenGet,
} from '@/client'
import type {
  DiagnosticDetail,
  DiagnosticResultResponse,
  DiagnosticSubmission,
  DiagnosticSummary,
  ExamDetail,
  ExamResultResponse,
  ExamSubmission,
  ExamSummary,
  InviteCreateRequest,
  InviteCreatedResponse,
  InviteValidationResponse,
  LoginRequest,
  ProgressResponse,
  RegisterRequest,
  UserResponse,
} from '@/client'

/** An API call that returned a non-2xx response. */
export class ApiError extends Error {
  readonly status: number
  readonly body: unknown

  constructor(status: number, body: unknown) {
    super(`API request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

/**
 * Unwrap a generated `{ data, error, response }` result into `data`, throwing
 * an {@link ApiError} on a non-2xx response so promises reject normally.
 */
async function unwrap<T>(
  promise: Promise<{ data?: T; error?: unknown; response: Response }>
): Promise<T> {
  const { data, error, response } = await promise
  if (!response.ok || error !== undefined) {
    throw new ApiError(response.status, error ?? data)
  }
  return data as T
}

// --- Auth -----------------------------------------------------------------

export function login(body: LoginRequest): Promise<UserResponse> {
  return unwrap(loginApiV1AuthLoginPost({ body }))
}

export function logout(): Promise<unknown> {
  return unwrap(logoutApiV1AuthLogoutPost())
}

export function getMe(): Promise<UserResponse> {
  return unwrap(meApiV1AuthMeGet())
}

export function register(body: RegisterRequest): Promise<UserResponse> {
  return unwrap(registerApiV1AuthRegisterPost({ body }))
}

export function validateInvite(token: string): Promise<InviteValidationResponse> {
  return unwrap(validateInviteApiV1AuthInvitesTokenGet({ path: { token } }))
}

export function createInvite(body: InviteCreateRequest): Promise<InviteCreatedResponse> {
  return unwrap(createInviteApiV1InvitesPost({ body }))
}

// --- Catalog --------------------------------------------------------------

export function listExams(contest?: string): Promise<ExamSummary[]> {
  return unwrap(listExamsApiV1ExamsGet({ query: contest ? { contest } : undefined }))
}

export function getExam(examId: string): Promise<ExamDetail> {
  return unwrap(getExamApiV1ExamsExamIdGet({ path: { exam_id: examId } }))
}

export function listDiagnostics(): Promise<DiagnosticSummary[]> {
  return unwrap(listDiagnosticsApiV1DiagnosticsGet())
}

export function getDiagnostic(instrumentId: string): Promise<DiagnosticDetail> {
  return unwrap(
    getDiagnosticApiV1DiagnosticsInstrumentIdGet({
      path: { instrument_id: instrumentId },
    })
  )
}

// --- Attempts -------------------------------------------------------------

export function submitExam(examId: string, body: ExamSubmission): Promise<ExamResultResponse> {
  return unwrap(submitExamApiV1ExamsExamIdAttemptsPost({ path: { exam_id: examId }, body }))
}

export function submitDiagnostic(
  instrumentId: string,
  body: DiagnosticSubmission
): Promise<DiagnosticResultResponse> {
  return unwrap(
    submitDiagnosticApiV1DiagnosticsInstrumentIdAttemptsPost({
      path: { instrument_id: instrumentId },
      body,
    })
  )
}

// --- Progress -------------------------------------------------------------

export function getMyProgress(): Promise<ProgressResponse> {
  return unwrap(getMyProgressApiV1ProgressGet())
}

export function getUserProgress(userId: string): Promise<ProgressResponse> {
  return unwrap(getUserProgressApiV1UsersUserIdProgressGet({ path: { user_id: userId } }))
}
